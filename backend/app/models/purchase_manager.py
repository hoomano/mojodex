import os
from datetime import datetime, timedelta

import pytz
import stripe
from mojodex_backend_logger import MojodexBackendLogger

from app import db
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *

from mojodex_core.mail import send_admin_email
from sqlalchemy import and_, func, or_, text
from sqlalchemy.sql.functions import coalesce
from packaging import version


class PurchaseManager:
    logger_prefix = "Purchase Manager:: "
    user_before_version_046_category = "user_before_version_046"
    purchase_status_free_trial = "free_trial"
    purchase_status_active = "active"
    purchase_status_no_purchase = "no_purchase"
    purchases_email_receivers = os.environ["PURCHASES_EMAIL_RECEIVERS"].split(",") if "PURCHASES_EMAIL_RECEIVERS" in os.environ else []


    def __init__(self):
        self.logger = MojodexBackendLogger(
            f"{PurchaseManager.logger_prefix}")
        if "STRIPE_API_KEY" in os.environ:
            stripe.api_key = os.environ["STRIPE_API_KEY"]

    def check_user_active_purchases(self, user_id):
        """
        Returns whether user has an active purchase the name of the product the user has purchased, and the number of remaining days of free trial if applicable
        :param user_id:
        :return:
        """
        try:
            user_active_purchases = self.__user_active_purchases(user_id)
            if not user_active_purchases:  # the user has no active purchase
                return []
            else:
                current_purchases = []
                for user_active_purchase in user_active_purchases:
                    # check purchase validity
                    if user_active_purchase["is_free_product"]:  # Product is free
                        self.logger.info("Product is free")
                    elif user_active_purchase["custom_purchase_id"]:
                        # the purchase is managed by Backoffice
                        self.logger.info("Purchase managed by Backoffice")
                    elif user_active_purchase["subscription_stripe_id"]:  # purchase is a subscription and has been done through stripe
                        # check purchase is_active (subscription has been paid) using stripe api Retrieve subscription
                        try:
                            if stripe.Subscription.retrieve(
                                    user_active_purchase["subscription_stripe_id"]).status == "active":
                                self.logger.info("Purchase paid with Stripe")
                        except Exception as e:
                            send_admin_email(
                                subject=f"URGENT: STRIPE API FAILED TO CHECK PURCHASE {user_active_purchase['purchase_pk']}",
                                recipients=self.purchases_email_receivers,
                                text=f"Stripe API error: {e}")
                    elif user_active_purchase["session_stripe_id"] and user_active_purchase["completed_date"]:  # purchase is NOT a subscription and has been done through stripe
                        self.logger.info("Purchase paid with Stripe")
                    elif user_active_purchase[
                        "apple_transaction_id"]:  # purchase has been done through apple in-app purchase
                        self.logger.info("Purchase paid with Apple")
                    else:
                        # if not, then there is a strange problem, let's send a message to admin
                        message = f"Purchase {user_active_purchase['purchase_pk']} of user {user_id} has no stripe_id nor apple_transaction_id nor custom_purchase_id and is not free." \
                                  f"\nPlease check this purchase."
                        send_admin_email(subject="URGENT: Incorrect purchase in db",
                                         recipients=self.purchases_email_receivers,
                                         text=message)
                        try:
                            self.__deactivate_purchase_from_purchase_pk(user_active_purchase['purchase_pk'])
                            db.session.commit()
                        except Exception as e:
                            self.logger.error(
                                f"Error deactivating purchase {user_active_purchase['purchase_pk']} : {e}")
                        continue
                    current_purchases.append({"product_name": user_active_purchase["product_name"],
                                              "remaining_days": user_active_purchase["purchase_remaining_days"],
                                              "n_validity_days": user_active_purchase["product_n_validity_days"],
                                              "n_tasks_limit": user_active_purchase["product_n_tasks_limit"],
                                              "n_tasks_consumed": user_active_purchase["n_tasks_consumed"],
                                              "tasks": user_active_purchase["product_tasks"],
                                              "is_free_product": user_active_purchase["is_free_product"]})

            return current_purchases
        except Exception as e:
            raise Exception(f"PurchaseManager :: check_user_active_purchases : {e}")

    def __get_stripe_price(self, product_stripe_id):
        try:
            stripe_price = stripe.Price.list(product=product_stripe_id).data[0]
            if stripe_price["currency"] == "usd":
                return f"${stripe_price['unit_amount'] / 100}"
            elif stripe_price["currency"] == "eur":
                return f"{stripe_price['unit_amount'] / 100}€"
            else:
                return None
        except Exception as e:
            raise Exception(f"PurchaseManager :: __get_stripe_price : {e}")

    def __user_active_purchases(self, user_id):
        """
        This function returns the active purchases for a user.
        There can be one or several active purchases for a user.
        """
        try:
            user_language_code = db.session.query(MdUser.language_code).filter(MdUser.user_id == user_id).first()
            user_language_code = user_language_code[0] if user_language_code else "en"


            remaining_days = (
                    text('md_product.n_days_validity * interval \'1 day\'') - (
                    func.now() - MdPurchase.creation_date) + timedelta(days=1)
            )

            results = db.session.query(
                    MdPurchase, 
                    MdProduct, 
                    func.json_object_agg(
                        MdProductDisplayedData.language_code,
                        MdProductDisplayedData.name
                    ).label("product_displayed_data"),
                    MdProductCategory, 
                    remaining_days.label("remaining_days")
                ) \
                .join(MdProduct, MdProduct.product_pk == MdPurchase.product_fk) \
                .join(MdProductDisplayedData, MdProductDisplayedData.product_fk == MdProduct.product_pk) \
                .join(MdProductCategory, MdProductCategory.product_category_pk == MdProduct.product_category_fk) \
                .filter(MdPurchase.user_id == user_id) \
                .filter(MdPurchase.active) \
                .order_by(MdPurchase.creation_date.desc()) \
                .group_by(
                    MdPurchase, 
                    MdProduct.product_pk, 
                    MdProductDisplayedData.product_fk,
                    MdProductCategory
                ) \
                .all()
            if not results:
                return []

            results = [result._asdict() for result in results]

            return [{"purchase_pk": result["MdPurchase"].purchase_pk,
                     "subscription_stripe_id": result["MdPurchase"].subscription_stripe_id,
                     "session_stripe_id": result["MdPurchase"].session_stripe_id,
                     "completed_date": result["MdPurchase"].completed_date,
                     "apple_transaction_id": result["MdPurchase"].apple_transaction_id,
                     "custom_purchase_id": result["MdPurchase"].custom_purchase_id,
                     "purchase_remaining_days": result["remaining_days"].days if result["remaining_days"] else None,
                     "n_tasks_consumed": self.__purchase_tasks_consumption(result["MdPurchase"].purchase_pk),
                     "product_name": result["product_displayed_data"][user_language_code] 
                        if user_language_code in result["product_displayed_data"]
                        else result["product_displayed_data"]["en"],
                     "is_free_product": result["MdProduct"].free,
                     "product_n_tasks_limit": result["MdProduct"].n_tasks_limit,
                     "product_n_validity_days": result["MdProduct"].n_days_validity,
                     "product_tasks": self.__get_product_tasks(result["MdProduct"], user_id)} for result in
                    results]

        except Exception as e:
            raise Exception(f"__user_active_purchases : {e}")

    def __get_product_tasks(self, product, user_id):
        try:
            # Subquery to retrieve the tasks in the user_language_code
            user_lang_subquery = (
                db.session.query(
                    MdTaskDisplayedData.task_fk.label("task_fk"),
                    MdTaskDisplayedData.name_for_user.label("user_lang_name_for_user"),
                )
                .join(MdUser, MdUser.user_id == user_id)
                .filter(MdTaskDisplayedData.language_code == MdUser.language_code)
                .subquery()
            )

            # Subquery to retrieve the tasks in 'en'
            en_subquery = (
                db.session.query(
                    MdTaskDisplayedData.task_fk.label("task_fk"),
                    MdTaskDisplayedData.name_for_user.label("en_name_for_user"),
                )
                .filter(MdTaskDisplayedData.language_code == "en")
                .subquery()
            )
                
            product_tasks = (
                db.session.query(
                    MdTaskDisplayedData.task_fk.label("task_fk"),
                    coalesce(
                        user_lang_subquery.c.user_lang_name_for_user,
                        en_subquery.c.en_name_for_user
                    ).label("name_for_user")
                )
                .outerjoin(user_lang_subquery, user_lang_subquery.c.task_fk == MdTaskDisplayedData.task_fk)
                .outerjoin(en_subquery, en_subquery.c.task_fk == MdTaskDisplayedData.task_fk)
                .join(MdTask, MdTask.task_pk == MdTaskDisplayedData.task_fk)
                .join(MdProductTask, MdProductTask.task_fk == MdTask.task_pk)
                .filter(MdProductTask.product_fk == product.product_pk)
                .group_by(
                    MdTaskDisplayedData.task_fk,
                    user_lang_subquery.c.user_lang_name_for_user,
                    en_subquery.c.en_name_for_user
                )
                .all())
        
            return [product_task.name_for_user for product_task in product_tasks]
        except Exception as e:
            raise Exception(f"__get_product_tasks : {e}")

    def user_has_active_subscription(self, user_id):
        try:
            user_subscriptions = db.session.query(MdPurchase) \
                .join(MdProduct, MdProduct.product_pk == MdPurchase.product_fk) \
                .filter(MdPurchase.user_id == user_id) \
                .filter(MdPurchase.active == True) \
                .filter(and_(MdProduct.n_days_validity.is_(None), MdProduct.n_tasks_limit.is_(None))) \
                .count()
            return user_subscriptions > 0
        except Exception as e:
            raise Exception(f"user_has_active_subscription : {e}")

    def get_purchasable_products(self, user_id):
        try:
            # Get user's current category
            product_category_pk, user_language_code = (
                db.session.query(
                    MdUser.product_category_fk,
                    MdUser.language_code
                )
                .filter(MdUser.user_id == user_id)
            ).first()

            if product_category_pk is None:
                return []

            # User can buy any product of the same category that is not free
            # If they already have a subscription (product.n_days_validity = None && product.n_tasks_limit = None, they can't buy another one
            # All not free products of same category
            purchasable_products = (
                db.session.query(
                    MdProduct,
                    func.json_object_agg(
                        MdProductDisplayedData.language_code,
                        MdProductDisplayedData.name
                    ).label("product_displayed_data"),
                )
                .join(MdProductDisplayedData, MdProductDisplayedData.product_fk == MdProduct.product_pk)
                .filter(MdProduct.product_category_fk == product_category_pk)
                .filter(MdProduct.free == False)
                .filter(MdProduct.status == "active")
                .group_by(
                    MdProduct.product_pk,
                    MdProductDisplayedData.product_fk
                )
            )

            # Does user has an active subscription ?
            if self.user_has_active_subscription(user_id):
                # filter out subscription products with n_days_validity
                purchasable_products = purchasable_products.filter(or_(MdProduct.n_days_validity.isnot(None), MdProduct.n_tasks_limit.isnot(None)))

            purchasable_products = purchasable_products.all()

            # get user language
            user_language = db.session.query(MdUser.language_code) \
                .filter(MdUser.user_id == user_id) \
                .first()
            user_language = user_language[0] if user_language else "en"

            return [{"product_pk": purchasable_product.product_pk,
                     "name": product_displayed_data[user_language_code]
                        if user_language_code in product_displayed_data 
                        else product_displayed_data["en"],
                     "product_stripe_id": purchasable_product.product_stripe_id,
                     "product_apple_id": purchasable_product.product_apple_id,
                     "n_days_validity": purchasable_product.n_days_validity,
                     "n_tasks_limit": purchasable_product.n_tasks_limit,
                     "stripe_price": self.__get_stripe_price(
                         purchasable_product.product_stripe_id) if purchasable_product.product_stripe_id else None,
                     "tasks": self.__get_product_tasks(purchasable_product, user_id)
                    } for purchasable_product, product_displayed_data in purchasable_products]

        except Exception as e:
            raise Exception(f"__get_purchasable_products : {e}")

    def purchase_for_new_task(self, user_task_pk):
        try:
            # Query for active purchases of the user that give access to the task
            active_purchases = db.session.query(MdPurchase) \
                .join(MdUser, MdPurchase.user_id == MdUser.user_id) \
                .join(MdUserTask, MdUserTask.user_id == MdUser.user_id) \
                .join(MdProduct, MdProduct.product_pk == MdPurchase.product_fk) \
                .join(MdProductTask, and_(MdProductTask.product_fk == MdProduct.product_pk,
                                          MdUserTask.task_fk == MdProductTask.task_fk)) \
                .filter(MdUserTask.user_task_pk == user_task_pk) \
                .filter(MdPurchase.active == True) \
                .all()

            # Create a subquery to get the counts of MdUserTaskExecution per purchase
            count_executions_subquery = db.session.query(MdUserTaskExecution.purchase_fk,
                                                         func.count().label("executions_count")) \
                .group_by(MdUserTaskExecution.purchase_fk) \
                .subquery()

            # Get the first purchase with n_tasks_limit > nb of user_task_execution
            first_suitable_purchase = db.session.query(MdPurchase) \
                .join(MdProduct, MdPurchase.product_fk == MdProduct.product_pk) \
                .outerjoin(count_executions_subquery, MdPurchase.purchase_pk == count_executions_subquery.c.purchase_fk) \
                .filter(MdPurchase.purchase_pk.in_([purchase.purchase_pk for purchase in active_purchases])) \
                .filter(or_(MdProduct.n_tasks_limit.is_(None),
                            MdProduct.n_tasks_limit > count_executions_subquery.c.executions_count,
                            count_executions_subquery.c.executions_count.is_(None))) \
                .order_by(MdPurchase.creation_date) \
                .first()

            return first_suitable_purchase

        except Exception as e:
            raise Exception(f"{self.logger_prefix} can_create_new_task : {e}")

    def associate_purchase_to_user_task_execution(self, user_task_execution_pk):
        try:
            user_task_execution = db.session.query(MdUserTaskExecution) \
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk).first()
            if user_task_execution.purchase_fk:
                return None
            purchase = self.purchase_for_new_task(user_task_execution.user_task_fk)
            if purchase:
                user_task_execution.purchase_fk = purchase.purchase_pk
                db.session.commit()

                return purchase
            else:
                raise Exception(f"No suitable purchase found")
        except Exception as e:
            raise Exception(
                f"{self.logger_prefix} :: associate_purchase_to_user_task_execution - user_task_execution {user_task_execution_pk}: {e}")

    def __purchase_tasks_consumption(self, purchase_pk):
        try:
            count_user_task_execution = db.session.query(MdUserTaskExecution) \
                .filter(MdUserTaskExecution.purchase_fk == purchase_pk) \
                .count()
            return count_user_task_execution if count_user_task_execution else 0
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __purchase_tasks_consumption - purchase {purchase_pk}: {e}")

    def purchase_is_all_consumed(self, purchase_pk):
        try:
            # count how many user_task_execution are associated to this purchase
            count_user_task_execution = self.__purchase_tasks_consumption(purchase_pk)

            product_n_tasks_limit = db.session.query(MdProduct.n_tasks_limit) \
                .join(MdPurchase, MdPurchase.product_fk == MdProduct.product_pk) \
                .filter(MdPurchase.purchase_pk == purchase_pk) \
                .first()[0]

            return count_user_task_execution >= product_n_tasks_limit if product_n_tasks_limit else False
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: purchase_is_all_consumed - purchase {purchase_pk}: {e}")

    def get_last_expired_purchases(self, user_id):
        try:
            last_expired_purchases = []
            last_expired_package = self.__get_last_expired_package(user_id)
            last_expired_subscription = self.__get_last_expired_subscription(user_id)

            # get user language
            user_language = db.session.query(MdUser.language_code) \
                .filter(MdUser.user_id == user_id) \
                .first()[0]

            if last_expired_package:
                last_expired_package, last_expired_package_product, last_expired_package_product_name, remaining_days = last_expired_package
                last_expired_purchases.append({
                    "product_name": last_expired_package_product_name,
                    "tasks": self.__get_product_tasks(last_expired_package_product, user_id),
                    "remaining_days": remaining_days,
                    "n_tasks_limit": last_expired_package_product.n_tasks_limit,
                    "n_days_validity": last_expired_package_product.n_days_validity,
                    "is_free_product": last_expired_package_product.free,
                    "n_tasks_consumed": self.__purchase_tasks_consumption(last_expired_package.purchase_pk),
                })

            if last_expired_subscription:
                last_expired_subscription, last_expired_subscription_product, last_expired_subscription_product_name, remaining_days = last_expired_subscription
                if not last_expired_package or (
                        last_expired_package and last_expired_subscription.purchase_pk != last_expired_package.purchase_pk):
                    last_expired_purchases.append({
                        "product_name": last_expired_subscription_product_name,
                        "tasks": self.__get_product_tasks(last_expired_subscription_product, user_id),
                        "remaining_days": remaining_days,
                        "n_tasks_limit": last_expired_subscription_product.n_tasks_limit,
                        "n_days_validity": last_expired_subscription_product.n_days_validity,
                        "is_free_product": last_expired_subscription_product.free,
                        "n_tasks_consumed": self.__purchase_tasks_consumption(last_expired_subscription.purchase_pk),
                    })
            return last_expired_purchases
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: get_last_expired_purchases - user {user_id}: {e}")

    def __get_last_expired_package(self, user_id):
        try:
            remaining_days = (
                    text('md_product.n_days_validity * interval \'1 day\'') - (
                    func.now() - MdPurchase.creation_date) + timedelta(days=1)
            )

            # Get last expired package
            user_language_code = db.session.query(MdUser.language_code).filter(MdUser.user_id == user_id).first()[0]
            last_expired_package = (
                db.session.query(
                    MdPurchase, 
                    MdProduct,
                    MdProductDisplayedData.name.label("product_name"),
                    remaining_days.label("remaining_days")
                )
                .join(MdProduct, MdProduct.product_pk == MdPurchase.product_fk)
                .join(MdProductDisplayedData, MdProductDisplayedData.product_fk == MdProduct.product_pk)
                .filter(
                    or_(
                        MdProductDisplayedData.language_code == user_language_code,
                        MdProductDisplayedData.language_code == 'en'
                    )
                )
                .order_by(
                    # Sort by user's language first otherwise by english
                    func.nullif(MdProductDisplayedData.language_code, 'en').asc()
                )
                .filter(MdPurchase.user_id == user_id)
                .filter(MdPurchase.active == False)
                .filter(MdProduct.n_tasks_limit.isnot(None))
                .order_by(MdPurchase.creation_date.desc())
                .first())
            if not last_expired_package:
                return None
            else:
                last_expired_package = last_expired_package._asdict()
            return last_expired_package["MdPurchase"], last_expired_package["MdProduct"], last_expired_package["product_name"], \
                last_expired_package["remaining_days"].days if last_expired_package["remaining_days"] else None
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __get_last_expired_package - user {user_id}: {e}")

    def __get_last_expired_subscription(self, user_id):
        try:
            remaining_days = (
                    text('md_product.n_days_validity * interval \'1 day\'') - (
                    func.now() - MdPurchase.creation_date) + timedelta(days=1)
            )
            # Get last expired subscription
            user_language_code = db.session.query(MdUser.language_code).filter(MdUser.user_id == user_id).first()[0]
            last_expired_subscription = (
                db.session.query(
                    MdPurchase, 
                    MdProduct, 
                    MdProductDisplayedData.name.label("product_name"),
                    remaining_days.label("remaining_days")
                )
                .join(MdProduct, MdProduct.product_pk == MdPurchase.product_fk)
                .join(MdProductDisplayedData, MdProductDisplayedData.product_fk == MdProduct.product_pk)
                .filter(
                    or_(
                        MdProductDisplayedData.language_code == user_language_code,
                        MdProductDisplayedData.language_code == 'en'
                    )
                )
                .order_by(
                    # Sort by user's language first otherwise by english
                    func.nullif(MdProductDisplayedData.language_code, 'en').asc()
                )
                .filter(MdPurchase.user_id == user_id)
                .filter(MdPurchase.active == False)
                .filter(MdProduct.n_days_validity.isnot(None))
                .order_by(MdPurchase.creation_date.desc())
                .first())
            if not last_expired_subscription:
                return None
            else:
                last_expired_subscription = last_expired_subscription._asdict()
            return last_expired_subscription["MdPurchase"], last_expired_subscription["MdProduct"], last_expired_subscription["product_name"], \
                last_expired_subscription["remaining_days"].days if last_expired_subscription["remaining_days"] else None
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __get_last_expired_subscription - user {user_id}: {e}")

    def activate_purchase(self, purchase):
        try:

            # if purchase is subscription  or free trial and user has active subscription, deactivate it
            # also deactivate free trial
            purchase_product = db.session.query(MdProduct).filter(MdProduct.product_pk == purchase.product_fk).first()
            product_is_free_trial = purchase_product.free and (
                        purchase_product.n_days_validity or purchase_product.n_tasks_limit)
            product_is_subscription = not purchase_product.n_days_validity and not purchase_product.n_tasks_limit
            if product_is_free_trial or product_is_subscription:
                user_active_subscription = db.session.query(MdPurchase) \
                    .join(MdProduct, MdProduct.product_pk == MdPurchase.product_fk) \
                    .filter(MdPurchase.user_id == purchase.user_id) \
                    .filter(MdPurchase.active == True) \
                    .filter(or_(and_(MdProduct.n_days_validity.is_(None), MdProduct.n_tasks_limit.is_(None)), and_(MdProduct.free,
                                                                          or_(MdProduct.n_days_validity.isnot(None),
                                                                              MdProduct.n_tasks_limit.isnot(None))))) \
                .first()
                if user_active_subscription:
                    self.deactivate_purchase(user_active_subscription)

            # enable user tasks from this purchase
            # Add tasks from product_task to user_task
            tasks = db.session.query(MdTask) \
                .join(MdProductTask, MdProductTask.task_fk == MdTask.task_pk) \
                .filter(MdProductTask.product_fk == purchase.product_fk).all()

            for task in tasks:
                # if task not already in user_task, add it, else, enable it
                user_task = db.session.query(MdUserTask) \
                    .filter(MdUserTask.user_id == purchase.user_id) \
                    .filter(MdUserTask.task_fk == task.task_pk).first()

                if not user_task:
                    user_task = MdUserTask(
                        user_id=purchase.user_id,
                        task_fk=task.task_pk
                    )
                    db.session.add(user_task)
                else:
                    user_task.enabled = True
                db.session.flush()
            purchase.active = True

            # If user has no goal, associate the implicit_goal of corresponding product
            try:
                user = db.session.query(MdUser).filter(MdUser.user_id == purchase.user_id).first()
                if not user.goal:
                    implicit_product_goal = db.session.query(MdProductCategory.implicit_goal) \
                        .join(MdProduct, MdProduct.product_category_fk == MdProductCategory.product_category_pk) \
                        .filter(MdProduct.product_pk == purchase.product_fk).first()
                    if implicit_product_goal:
                        user.goal = implicit_product_goal[0]
            except Exception as e:
                log_error(f"Error while associating implicit goal to user: {e}")
        except Exception as e:
            raise Exception(f"{PurchaseManager.logger_prefix} activate_purchase : {e}")

    def __deactivate_purchase_from_purchase_pk(self, purchase_pk):
        try:
            purchase = db.session.query(MdPurchase).filter(MdPurchase.purchase_pk == purchase_pk).first()
            self.deactivate_purchase(purchase)
        except Exception as e:
            raise Exception(f"{PurchaseManager.logger_prefix} deactivate_purchase_from_purchase_pk : {e}")

    def deactivate_purchase(self, purchase):
        try:
            # select all user_tasks that are enabled by other active purchases
            to_keep_enabled_user_tasks = db.session.query(MdUserTask.user_task_pk) \
                .join(MdPurchase, MdPurchase.user_id == MdUserTask.user_id) \
                .filter(MdPurchase.active == True) \
                .join(MdProduct, MdProduct.product_pk == MdPurchase.product_fk) \
                .join(MdProductTask, and_(MdProductTask.product_fk == MdProduct.product_pk,
                                          MdUserTask.task_fk == MdProductTask.task_fk)) \
                .filter(MdPurchase.purchase_pk != purchase.purchase_pk) \
                .filter(MdUserTask.user_id == purchase.user_id) \
                .all()
            to_keep_enabled_user_tasks = [user_task[0] for user_task in to_keep_enabled_user_tasks]

            # select all user_tasks that need to be disabled (= user_tasks that are not enabled by other active purchases)
            user_tasks_to_disable = db.session.query(MdUserTask) \
                .filter(MdUserTask.user_id == purchase.user_id) \
                .filter(MdUserTask.enabled == True) \
                .filter(MdUserTask.user_task_pk.notin_(to_keep_enabled_user_tasks)) \
                .all()

            self.__deactivate_user_tasks(user_tasks_to_disable)
            purchase.active = False
        except Exception as e:
            raise Exception(f"{PurchaseManager.logger_prefix} deactivate_purchase : {e}")

    def __deactivate_user_tasks(self, user_tasks_to_disable):
        try:
            for user_task in user_tasks_to_disable:
                user_task.enabled = False
                db.session.flush()
        except Exception as e:
            raise Exception(f"{PurchaseManager.logger_prefix} deactivate_user_tasks : {e}")
