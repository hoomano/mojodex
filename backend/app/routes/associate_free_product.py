import os


from bs4 import BeautifulSoup
from jinja2 import Template
from flask import request
from flask_restful import Resource
from app import authenticate, db
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import MdPurchase, MdProduct, MdProductCategory, MdUser, MdEvent
from models.purchase_manager import PurchaseManager

from mojodex_core.email_sender.email_service import EmailService
from sqlalchemy import or_
from datetime import datetime

class FreeProductAssociation(Resource):
    welcome_email_dir = "mojodex_core/mails_templates/welcome"

    def __init__(self):
        FreeProductAssociation.method_decorators = [authenticate()]

    def put(self, user_id):
        error_message = "Error associating free product"
        if not request.is_json:
            log_error(f"{error_message}: Request must be JSON", notify_admin=True)
            return {"error": "Request must be JSON"}, 400

        try:
            timestamp = request.json["datetime"]
            product_category_pk = request.json["product_category_pk"]
        except KeyError as e:
            log_error(f"{error_message} - request.json: {request.json}: Missing field {e}", notify_admin=True)
            return {"error": f"Missing field {e}"}, 400

        try:
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
            if user is None:
                log_error(f"{error_message} user_id {user_id} does not exist", notify_admin=True)
                return {"error": f"user_id {user_id} does not exist"}, 400

            # Check user never had any purchase (even expired)
            user_free_purchase = db.session.query(MdPurchase)\
                .filter(MdPurchase.user_id == user_id)\
                .first()
            if user_free_purchase is not None:
                log_error(f"{error_message} user_id {user_id} asked for a free plan but already had a purchase", notify_admin=True)
                return {"error": f"user_id {user_id} already had a purchase"}, 400

            # Check product_category exists
            product_category = db.session.query(MdProductCategory).filter(MdProductCategory.product_category_pk == product_category_pk).first()
            if product_category is None:
                log_error(f"{error_message} user_id {user_id} - product_category_pk {product_category_pk} does not exist", notify_admin=True)
                return {"error": f"product_category_pk {product_category_pk} does not exist"}, 400

            # Associate category to user
            user.product_category_fk = product_category_pk
            # Associate category goal to user
            user.goal = product_category.implicit_goal


            # Find limited free product associated with product_category
            product = db.session.query(MdProduct)\
                .filter(MdProduct.product_category_fk == product_category_pk)\
                .filter(MdProduct.free == True) \
                .filter(or_(MdProduct.n_days_validity.isnot(None), MdProduct.n_tasks_limit.isnot(None))) \
                .first()

            if product is None:
                log_error(f"{error_message} user_id: {user_id} email: {user.email} - product_category_pk {product_category_pk} has no limited free product associated", notify_admin=True)
                return {"error": f"product_category_pk {product_category_pk} has no limited free product associated"}, 400

            # Create purchase
            purchase = MdPurchase(
                user_id=user_id,
                product_fk=product.product_pk,
                creation_date=datetime.now()
            )
            db.session.add(purchase)
            db.session.flush()

            # Activate purchase
            purchase_manager = PurchaseManager()
            purchase_manager.activate_purchase(purchase)

            db.session.commit()

            try:
                message = f"Free product {product.label} associated for user user_id: {user_id} email: {user.email}"
                EmailService().send(subject="Free product associated",
                                 recipients=PurchaseManager.purchases_email_receivers,
                                 text=message)
            except Exception as e:
                log_error(f"Error sending mail : {e}")

            current_purchases = purchase_manager.check_user_active_purchases(user_id)
            purchasable_products = purchase_manager.get_purchasable_products(user_id)

            try:
                # Now, let's send a welcome email to the user !
                email_language = user.language_code if user.language_code else "en"
                category = product_category.label
                email_file = os.path.join(self.welcome_email_dir, email_language, category + ".html")

                # check if email file exists
                if not os.path.isfile(email_file):
                    # change language to en
                    email_language = "en"
                    email_file = os.path.join(self.welcome_email_dir, email_language, category + ".html")

                with open(email_file, "r") as f:
                    email_content = Template(f.read()).render(mojodex_webapp_url=os.environ["MOJODEX_WEBAPP_URI"])

                try:
                    soup = BeautifulSoup(email_content, 'html.parser')
                    subject = soup.head.title.string
                    if not subject:
                        raise Exception("No subject found")
                except Exception as e:
                    log_error(f"Error parsing welcome email {email_file} : {e}", notify_admin=True)
                    subject = "Welcome to Mojodex"

                if EmailService().configured:
                    EmailService().send(subject=subject,
                                               recipients=[user.email],
                                               html_body=email_content)
                    # add notification to db
                    email_event = MdEvent(creation_date=datetime.now(), event_type='welcome_email',
                                          user_id=user_id,
                                          message={"subject": subject, "body": email_content, "email": user.email})
                    db.session.add(email_event)
                db.session.commit()

            except Exception as e:
                log_error(f"Error sending welcome email : {e}", notify_admin=True)


            return {
                "purchasable_products": purchasable_products,
                "current_purchases": current_purchases
            }, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} - request.json: {request.json}: {e}", notify_admin=True)
            return {"error": f"{error_message} : {e}"}, 400
