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


class RoleManager:
    logger_prefix = "Role Manager:: "
    user_before_version_046_category = "user_before_version_046"
    role_status_free_trial = "free_trial"
    role_status_active = "active"
    role_status_no_role = "no_role"
    roles_email_receivers = os.environ["PURCHASES_EMAIL_RECEIVERS"].split(",") if "PURCHASES_EMAIL_RECEIVERS" in os.environ else []


    def __init__(self):
        self.logger = MojodexBackendLogger(
            f"{RoleManager.logger_prefix}")
        if "STRIPE_API_KEY" in os.environ:
            stripe.api_key = os.environ["STRIPE_API_KEY"]

    def check_user_active_roles(self, user_id):
        """
        Returns whether user has an active role the name of the product the user has roled, and the number of remaining days of free trial if applicable
        :param user_id:
        :return:
        """
        try:
            user_active_roles = self.__user_active_roles(user_id)
            if not user_active_roles:  # the user has no active role
                return []
            else:
                current_roles = []
                for user_active_role in user_active_roles:
                    # check role validity
                    if user_active_role["is_free_product"]:  # Product is free
                        self.logger.info("Product is free")
                    elif user_active_role["custom_purchase_id"]:
                        # the role is managed by Backoffice
                        self.logger.info("Role managed by Backoffice")
                    elif user_active_role["subscription_stripe_id"]:  # role is a subscription and has been done through stripe
                        # check role is_active (subscription has been paid) using stripe api Retrieve subscription
                        try:
                            if stripe.Subscription.retrieve(
                                    user_active_role["subscription_stripe_id"]).status == "active":
                                self.logger.info("Role paid with Stripe")
                        except Exception as e:
                            send_admin_email(
                                subject=f"URGENT: STRIPE API FAILED TO CHECK ROLE {user_active_role['purchase_pk']}",
                                recipients=self.roles_email_receivers,
                                text=f"Stripe API error: {e}")
                    elif user_active_role["session_stripe_id"] and user_active_role["completed_date"]:  # role is NOT a subscription and has been done through stripe
                        self.logger.info("Role paid with Stripe")
                    elif user_active_role[
                        "apple_transaction_id"]:  # role has been done through apple in-app role
                        self.logger.info("Role paid with Apple")
                    else:
                        # if not, then there is a strange problem, let's send a message to admin
                        message = f"Role {user_active_role['purchase_pk']} of user {user_id} has no stripe_id nor apple_transaction_id nor custom_role_id and is not free." \
                                  f"\nPlease check this role."
                        send_admin_email(subject="URGENT: Incorrect role in db",
                                         recipients=self.roles_email_receivers,
                                         text=message)
                        try:
                            self.__deactivate_role_from_role_pk(user_active_role['purchase_pk'])
                            db.session.commit()
                        except Exception as e:
                            self.logger.error(
                                f"Error deactivating role {user_active_role['purchase_pk']} : {e}")
                        continue
                    current_roles.append({"product_name": user_active_role["product_name"],
                                              "remaining_days": user_active_role["purchase_remaining_days"],
                                              "n_validity_days": user_active_role["product_n_validity_days"],
                                              "n_tasks_limit": user_active_role["product_n_tasks_limit"],
                                              "n_tasks_consumed": user_active_role["n_tasks_consumed"],
                                              "tasks": user_active_role["product_tasks"],
                                              "is_free_product": user_active_role["is_free_product"]})

            return current_roles
        except Exception as e:
            raise Exception(f"RoleManager :: check_user_active_roles : {e}")

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
            raise Exception(f"RoleManager :: __get_stripe_price : {e}")

    def __user_active_roles(self, user_id):
        """
        This function returns the active roles for a user.
        There can be one or several active roles for a user.
        """
        try:
            user_language_code = db.session.query(MdUser.language_code).filter(MdUser.user_id == user_id).first()
            user_language_code = user_language_code[0] if user_language_code else "en"


            remaining_days = (
                    text('md_profile.n_days_validity * interval \'1 day\'') - (
                    func.now() - MdRole.creation_date) + timedelta(days=1)
            )

            results = db.session.query(
                    MdRole, 
                    MdProfile, 
                    func.json_object_agg(
                        MdProfileDisplayedData.language_code,
                        MdProfileDisplayedData.name
                    ).label("product_displayed_data"),
                    MdProfileCategory, 
                    remaining_days.label("remaining_days")
                ) \
                .join(MdProfile, MdProfile.profile_pk == MdRole.profile_fk) \
                .join(MdProfileDisplayedData, MdProfileDisplayedData.profile_fk == MdProfile.profile_pk) \
                .join(MdProfileCategory, MdProfileCategory.profile_category_pk == MdProfile.profile_category_fk) \
                .filter(MdRole.user_id == user_id) \
                .filter(MdRole.active) \
                .order_by(MdRole.creation_date.desc()) \
                .group_by(
                    MdRole, 
                    MdProfile.profile_pk, 
                    MdProfileDisplayedData.profile_fk,
                    MdProfileCategory
                ) \
                .all()
            if not results:
                return []

            results = [result._asdict() for result in results]

            return [{"purchase_pk": result["MdRole"].role_pk,
                     "subscription_stripe_id": result["MdRole"].subscription_stripe_id,
                     "session_stripe_id": result["MdRole"].session_stripe_id,
                     "completed_date": result["MdRole"].completed_date,
                     "apple_transaction_id": result["MdRole"].apple_transaction_id,
                     "custom_purchase_id": result["MdRole"].custom_role_id,
                     "purchase_remaining_days": result["remaining_days"].days if result["remaining_days"] else None,
                     "n_tasks_consumed": self.__role_tasks_consumption(result["MdRole"].role_pk),
                     "product_name": result["product_displayed_data"][user_language_code]
                        if user_language_code in result["product_displayed_data"]
                        else result["product_displayed_data"]["en"],
                     "is_free_product": result["MdProfile"].free,
                     "product_n_tasks_limit": result["MdProfile"].n_tasks_limit,
                     "product_n_validity_days": result["MdProfile"].n_days_validity,
                     "product_tasks": self.__get_product_tasks(result["MdProfile"], user_id)
                    } for result in results]

        except Exception as e:
            raise Exception(f"__user_active_roles : {e}")

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
                .join(MdProfileTask, MdProfileTask.task_fk == MdTask.task_pk)
                .filter(MdProfileTask.profile_fk == product.profile_pk)
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
            user_subscriptions = db.session.query(MdRole) \
                .join(MdProfile, MdProfile.profile_pk == MdRole.profile_fk) \
                .filter(MdRole.user_id == user_id) \
                .filter(MdRole.active == True) \
                .filter(and_(MdProfile.n_days_validity.is_(None), MdProfile.n_tasks_limit.is_(None))) \
                .count()
            return user_subscriptions > 0
        except Exception as e:
            raise Exception(f"user_has_active_subscription : {e}")

    def get_purchasable_products(self, user_id):
        try:

            # Get user's current category
            result = (
                db.session.query(
                    MdUser.profile_category_fk,
                    MdUser.language_code
                )
                .filter(MdUser.user_id == user_id)
            ).first()

            if result is None:
                return []
            
            profile_category_pk, user_language_code = result

            # User can buy any product of the same category that is not free
            # If they already have a subscription (product.n_days_validity = None && product.n_tasks_limit = None, they can't buy another one
            # All not free products of same category
            purchasable_products = (
                db.session.query(
                    MdProfile,
                    func.json_object_agg(
                        MdProfileDisplayedData.language_code,
                        MdProfileDisplayedData.name
                    ).label("product_displayed_data"),
                )
                .join(MdProfileDisplayedData, MdProfileDisplayedData.profile_fk == MdProfile.profile_pk)
                .filter(MdProfile.profile_category_fk == profile_category_pk)
                .filter(MdProfile.free == False)
                .filter(MdProfile.status == "active")
                .group_by(
                    MdProfile.profile_pk,
                    MdProfileDisplayedData.profile_fk
                )
            )
            # Does user has an active subscription ?
            if self.user_has_active_subscription(user_id):
                # filter out subscription products with n_days_validity
                purchasable_products = purchasable_products.filter(or_(MdProfile.n_days_validity.isnot(None), MdProfile.n_tasks_limit.isnot(None)))

            purchasable_products = purchasable_products.all()

            # get user language
            user_language = db.session.query(MdUser.language_code) \
                .filter(MdUser.user_id == user_id) \
                .first()
            user_language = user_language[0] if user_language else "en"

            return [{"product_pk": purchasable_product.profile_pk,
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

    def role_for_new_task(self, user_task_pk):
        try:
            # Query for active roles of the user that give access to the task
            active_roles = db.session.query(MdRole) \
                .join(MdUser, MdRole.user_id == MdUser.user_id) \
                .join(MdUserTask, MdUserTask.user_id == MdUser.user_id) \
                .join(MdProfile, MdProfile.profile_pk == MdRole.profile_fk) \
                .join(MdProfileTask, and_(MdProfileTask.profile_fk == MdProfile.profile_pk,
                                          MdUserTask.task_fk == MdProfileTask.task_fk)) \
                .filter(MdUserTask.user_task_pk == user_task_pk) \
                .filter(MdRole.active == True) \
                .all()

            # Create a subquery to get the counts of MdUserTaskExecution per role
            count_executions_subquery = db.session.query(MdUserTaskExecution.role_fk,
                                                         func.count().label("executions_count")) \
                .group_by(MdUserTaskExecution.role_fk) \
                .subquery()

            # Get the first role with n_tasks_limit > nb of user_task_execution
            first_suitable_role = db.session.query(MdRole) \
                .join(MdProfile, MdRole.profile_fk == MdProfile.profile_pk) \
                .outerjoin(count_executions_subquery, MdRole.role_pk == count_executions_subquery.c.role_fk) \
                .filter(MdRole.role_pk.in_([role.role_pk for role in active_roles])) \
                .filter(or_(MdProfile.n_tasks_limit.is_(None),
                            MdProfile.n_tasks_limit > count_executions_subquery.c.executions_count,
                            count_executions_subquery.c.executions_count.is_(None))) \
                .order_by(MdRole.creation_date) \
                .first()

            return first_suitable_role

        except Exception as e:
            raise Exception(f"{self.logger_prefix} can_create_new_task : {e}")

    def associate_role_to_user_task_execution(self, user_task_execution_pk):
        try:
            user_task_execution = db.session.query(MdUserTaskExecution) \
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk).first()
            if user_task_execution.role_fk:
                return None
            role = self.role_for_new_task(user_task_execution.user_task_fk)
            if role:
                user_task_execution.role_fk = role.role_pk
                db.session.commit()

                return role
            else:
                raise Exception(f"No suitable role found")
        except Exception as e:
            raise Exception(
                f"{self.logger_prefix} :: associate_role_to_user_task_execution - user_task_execution {user_task_execution_pk}: {e}")



    def __role_tasks_consumption(self, role_pk):
        try:
            count_user_task_execution = db.session.query(MdUserTaskExecution) \
                .filter(MdUserTaskExecution.role_fk == role_pk) \
                .count()
            return count_user_task_execution if count_user_task_execution else 0
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __role_tasks_consumption - role {role_pk}: {e}")

    def role_is_all_consumed(self, role_pk):
        try:
            # count how many user_task_execution are associated to this role
            count_user_task_execution = self.__role_tasks_consumption(role_pk)

            product_n_tasks_limit = db.session.query(MdProfile.n_tasks_limit) \
                .join(MdRole, MdRole.profile_fk == MdProfile.profile_pk) \
                .filter(MdRole.role_pk == role_pk) \
                .first()[0]

            return count_user_task_execution >= product_n_tasks_limit if product_n_tasks_limit else False
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: role_is_all_consumed - role {role_pk}: {e}")

    def get_last_expired_roles(self, user_id):
        try:
            last_expired_roles = []
            last_expired_package = self.__get_last_expired_package(user_id)
            last_expired_subscription = self.__get_last_expired_subscription(user_id)

            if last_expired_package:
                last_expired_package, last_expired_package_product, last_expired_package_product_name, remaining_days = last_expired_package
                last_expired_roles.append({
                    "product_name": last_expired_package_product_name,
                    "tasks": self.__get_product_tasks(last_expired_package_product, user_id),
                    "remaining_days": remaining_days,
                    "n_tasks_limit": last_expired_package_product.n_tasks_limit,
                    "n_days_validity": last_expired_package_product.n_days_validity,
                    "is_free_product": last_expired_package_product.free,
                    "n_tasks_consumed": self.__role_tasks_consumption(last_expired_package.role_pk),
                })

            if last_expired_subscription:
                last_expired_subscription, last_expired_subscription_product, last_expired_subscription_product_name, remaining_days = last_expired_subscription
                if not last_expired_package or (
                        last_expired_package and last_expired_subscription.role_pk != last_expired_package.role_pk):
                    last_expired_roles.append({
                        "product_name": last_expired_subscription_product_name,
                        "tasks": self.__get_product_tasks(last_expired_subscription_product, user_id),
                        "remaining_days": remaining_days,
                        "n_tasks_limit": last_expired_subscription_product.n_tasks_limit,
                        "n_days_validity": last_expired_subscription_product.n_days_validity,
                        "is_free_product": last_expired_subscription_product.free,
                        "n_tasks_consumed": self.__role_tasks_consumption(last_expired_subscription.role_pk),
                    })
            return last_expired_roles
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: get_last_expired_roles - user {user_id}: {e}")

    def __get_last_expired_package(self, user_id):
        try:
            remaining_days = (
                    text('md_profile.n_days_validity * interval \'1 day\'') - (
                    func.now() - MdRole.creation_date) + timedelta(days=1)
            )

            # Get last expired package
            user_language_code = db.session.query(MdUser.language_code).filter(MdUser.user_id == user_id).first()
            user_language_code = user_language_code[0] if user_language_code else 'en'
            last_expired_package = (
                db.session.query(
                    MdRole, 
                    MdProfile,
                    MdProfileDisplayedData.name.label("product_name"),
                    remaining_days.label("remaining_days")
                )
                .join(MdProfile, MdProfile.profile_pk == MdRole.profile_fk)
                .join(MdProfileDisplayedData, MdProfileDisplayedData.profile_fk == MdProfile.profile_pk)
                .filter(
                    or_(
                        MdProfileDisplayedData.language_code == user_language_code,
                        MdProfileDisplayedData.language_code == 'en'
                    )
                )
                .order_by(
                    # Sort by user's language first otherwise by english
                    func.nullif(MdProfileDisplayedData.language_code, 'en').asc()
                )
                .filter(MdRole.user_id == user_id)
                .filter(MdRole.active == False)
                .filter(MdProfile.n_tasks_limit.isnot(None))
                .order_by(MdRole.creation_date.desc())
                .first())
            if not last_expired_package:
                return None
            else:
                last_expired_package = last_expired_package._asdict()
            return last_expired_package["MdRole"], last_expired_package["MdProfile"], last_expired_package["product_name"], \
                last_expired_package["remaining_days"].days if last_expired_package["remaining_days"] else None
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __get_last_expired_package - user {user_id}: {e}")

    def __get_last_expired_subscription(self, user_id):
        try:
            remaining_days = (
                    text('md_profile.n_days_validity * interval \'1 day\'') - (
                    func.now() - MdRole.creation_date) + timedelta(days=1)
            )
            # Get last expired subscription
            user_language_code = db.session.query(MdUser.language_code).filter(MdUser.user_id == user_id).first()
            user_language_code = user_language_code[0] if user_language_code else 'en'
            last_expired_subscription = (
                db.session.query(
                    MdRole, 
                    MdProfile, 
                    MdProfileDisplayedData.name.label("product_name"),
                    remaining_days.label("remaining_days")
                )
                .join(MdProfile, MdProfile.profile_pk == MdRole.profile_fk)
                .join(MdProfileDisplayedData, MdProfileDisplayedData.profile_fk == MdProfile.profile_pk)
                .filter(
                    or_(
                        MdProfileDisplayedData.language_code == user_language_code,
                        MdProfileDisplayedData.language_code == 'en'
                    )
                )
                .order_by(
                    # Sort by user's language first otherwise by english
                    func.nullif(MdProfileDisplayedData.language_code, 'en').asc()
                )
                .filter(MdRole.user_id == user_id)
                .filter(MdRole.active == False)
                .filter(MdProfile.n_days_validity.isnot(None))
                .order_by(MdRole.creation_date.desc())
                .first())
            if not last_expired_subscription:
                return None
            else:
                last_expired_subscription = last_expired_subscription._asdict()
            return last_expired_subscription["MdRole"], last_expired_subscription["MdProfile"], last_expired_subscription["product_name"], \
                last_expired_subscription["remaining_days"].days if last_expired_subscription["remaining_days"] else None
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __get_last_expired_subscription - user {user_id}: {e}")

    def activate_role(self, role):
        try:

            # if role is subscription  or free trial and user has active subscription, deactivate it
            # also deactivate free trial
            role_product = db.session.query(MdProfile).filter(MdProfile.profile_pk == role.profile_fk).first()
            product_is_free_trial = role_product.free and (
                        role_product.n_days_validity or role_product.n_tasks_limit)
            product_is_subscription = not role_product.n_days_validity and not role_product.n_tasks_limit
            if product_is_free_trial or product_is_subscription:
                user_active_subscription = db.session.query(MdRole) \
                    .join(MdProfile, MdProfile.profile_pk == MdRole.profile_fk) \
                    .filter(MdRole.user_id == role.user_id) \
                    .filter(MdRole.active == True) \
                    .filter(or_(and_(MdProfile.n_days_validity.is_(None), MdProfile.n_tasks_limit.is_(None)), and_(MdProfile.free,
                                                                          or_(MdProfile.n_days_validity.isnot(None),
                                                                              MdProfile.n_tasks_limit.isnot(None))))) \
                .first()
                if user_active_subscription:
                    self.deactivate_role(user_active_subscription)

            # enable user tasks from this role
            # Add tasks from product_task to user_task
            tasks = db.session.query(MdTask) \
                .join(MdProfileTask, MdProfileTask.task_fk == MdTask.task_pk) \
                .filter(MdProfileTask.profile_fk == role.profile_fk).all()

            for task in tasks:
                # if task not already in user_task, add it, else, enable it
                user_task = db.session.query(MdUserTask) \
                    .filter(MdUserTask.user_id == role.user_id) \
                    .filter(MdUserTask.task_fk == task.task_pk).first()

                if not user_task:
                    user_task = MdUserTask(
                        user_id=role.user_id,
                        task_fk=task.task_pk
                    )
                    db.session.add(user_task)
                else:
                    user_task.enabled = True
                db.session.flush()


            role.active = True

            # If user has no goal, associate the implicit_goal of corresponding product
            try:
                user = db.session.query(MdUser).filter(MdUser.user_id == role.user_id).first()
                if not user.goal:
                    implicit_product_goal = db.session.query(MdProfileCategory.implicit_goal) \
                        .join(MdProfile, MdProfile.profile_category_fk == MdProfileCategory.profile_category_pk) \
                        .filter(MdProfile.profile_pk == role.profile_fk).first()
                    if implicit_product_goal:
                        user.goal = implicit_product_goal[0]
            except Exception as e:
                log_error(f"Error while associating implicit goal to user: {e}")
        except Exception as e:
            raise Exception(f"{RoleManager.logger_prefix} activate_role : {e}")

    def __deactivate_role_from_role_pk(self, role_pk):
        try:
            role = db.session.query(MdRole).filter(MdRole.role_pk == role_pk).first()
            self.deactivate_role(role)
        except Exception as e:
            raise Exception(f"{RoleManager.logger_prefix} deactivate_role_from_role_pk : {e}")

    def deactivate_role(self, role):
        try:
            # select all user_tasks that are enabled by other active roles
            to_keep_enabled_user_tasks = db.session.query(MdUserTask.user_task_pk) \
                .join(MdRole, MdRole.user_id == MdUserTask.user_id) \
                .filter(MdRole.active == True) \
                .join(MdProfile, MdProfile.profile_pk == MdRole.profile_fk) \
                .join(MdProfileTask, and_(MdProfileTask.profile_fk == MdProfile.profile_pk,
                                          MdUserTask.task_fk == MdProfileTask.task_fk)) \
                .filter(MdRole.role_pk != role.role_pk) \
                .filter(MdUserTask.user_id == role.user_id) \
                .all()
            to_keep_enabled_user_tasks = [user_task[0] for user_task in to_keep_enabled_user_tasks]

            # select all user_tasks that need to be disabled (= user_tasks that are not enabled by other active roles)
            user_tasks_to_disable = db.session.query(MdUserTask) \
                .filter(MdUserTask.user_id == role.user_id) \
                .filter(MdUserTask.enabled == True) \
                .filter(MdUserTask.user_task_pk.notin_(to_keep_enabled_user_tasks)) \
                .all()

            self.__deactivate_user_tasks(user_tasks_to_disable)

            role.active = False
        except Exception as e:
            raise Exception(f"{RoleManager.logger_prefix} deactivate_role : {e}")

    def __deactivate_user_tasks(self, user_tasks_to_disable):
        try:
            for user_task in user_tasks_to_disable:
                user_task.enabled = False
                db.session.flush()
        except Exception as e:
            raise Exception(f"{RoleManager.logger_prefix} deactivate_user_tasks : {e}")

