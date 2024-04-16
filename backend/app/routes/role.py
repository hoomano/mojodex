import json
import os

import stripe
from flask import request
from flask_restful import Resource
from datetime import datetime
from app import authenticate, db
from mojodex_core.entities import *
from mojodex_core.mail import send_admin_email
from mojodex_core.logging_handler import log_error

from mojodex_backend_logger import MojodexBackendLogger

from models.role_manager import RoleManager
from packaging import version


class Role(Resource):
    logger_prefix = "Role Resource:: "

    def __init__(self):
        self.logger = MojodexBackendLogger(
            f"{Role.logger_prefix}")
        Role.method_decorators = [authenticate(methods=["GET", "PUT"])]

    def put(self, user_id):
        # This function is called when a stripe session is opened,
        # It create an inactive role
        if not request.is_json:
            log_error(f"Error adding role : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        try:
            timestamp = request.json["datetime"]
            stripe_session_id = request.json["stripe_session_id"]
            app_version = version.parse(request.json["version"]) if "version" in request.json else version.parse("0.0.0")
        except KeyError as e:
            log_error(f"Error adding role : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:

            product_stripe_id = request.json["product_stripe_id"]
            product = db.session.query(MdProfile).filter(MdProfile.product_stripe_id == product_stripe_id).first()
            if product is None:
                log_error(f"Error adding role : product_stripe_id {product_stripe_id} does not exist")
                return {"error": f"product_stripe_id {product_stripe_id} does not exist"}, 400

            role_manager = RoleManager()
            if not product.n_days_validity: # product is a subscription
                if role_manager.user_has_active_subscription(user_id):
                    return {"error": f"User already has an active subscription"}, 400
            role = MdRole(
                user_id=user_id,
                session_stripe_id=stripe_session_id,
                product_fk=product.product_pk,
                creation_date=datetime.now(),
                active=False
            )
            db.session.add(role)
            db.session.commit()
            db.session.refresh(role)
            return {"purchase_pk": role.role_pk}, 200
        except Exception as e:
            log_error(f"Error adding role: {e}")
            return {"error": f"Error adding role: {e}"}, 400


    def post(self):
        ## This is a stripe webhook called to activate a role <hen payment is completed
        try:
            if not request.is_json:
                log_error(f"Error adding role : Request must be JSON")
                return {"error": "Request must be JSON"}, 400
        except Exception as e:
            log_error(f"Error on stripe webhook end of role : Request must be JSON")
            return {"error": "Request must be JSON"}, 400


        try:
            signature = request.headers.get('stripe-signature')
            event = stripe.Webhook.construct_event(
                payload=request.data, sig_header=signature, secret=os.environ["STRIPE_WEBHOOK_SECRET_NEW_PURCHASE"])

            # Get the type of webhook event sent - used to check the status of PaymentIntents.
            event_type = event['type']
            if event_type != 'checkout.session.completed':
                log_error('Unhandled event type %s', event_type)
                return {"error": f"Unhandled event type : {event_type}"}, 500

            data = event['data']

            session_id = data['object']['id']
            customer_id = data['object']['customer']
            subscription_id = data['object']['subscription']


            # find associated role in db:
            role = db.session.query(MdRole).filter(MdRole.session_stripe_id == session_id).first()
            if role is None:
                log_error(f"Role with session_stripe_id {session_id} does not exist in mojodex db")
                customer_email = data['object']['customer_details']['email']
                message = f"A role error occurred for customer {customer_id} - {customer_email} " \
                            f"role session_id={session_id} was not found in db"
                send_admin_email(subject="URGENT: Role error",
                                           recipients=RoleManager.roles_email_receivers,
                                           text=message)

                return {"error": f"Role with session_stripe_id {session_id} does not exist in mojodex db"}, 400

            self.logger.debug(f"User trying to buy product: {Role.default_product_name}")


            role.customer_stripe_id = customer_id
            role.subscription_stripe_id = subscription_id
            role.completed_date=datetime.now()
            db.session.flush()

            # activate role
            role_manager = RoleManager()
            role_manager.activate_role(role)

            db.session.commit()
            user_email = db.session.query(MdUser.email).filter(MdUser.user_id == role.user_id).first()[0]

            product = db.session.query(MdProfile).filter(MdProfile.product_pk == role.product_fk).first()
            try:
                message = f"🎉 Congratulations ! {user_email} just bought {product.name} !"
                send_admin_email(subject="🥳 New client role",
                                           recipients=RoleManager.roles_email_receivers,
                                           text=message)
            except Exception as e:
                log_error(f"Error sending mail : {e}")

            return {"purchase_pk": role.role_pk}, 200

        except Exception as e:
            log_error(f"Error in stripe webhook validating role: {e}")
            message=f"A role error occurred : {e}\n" \
                    f"See [https://dashboard.stripe.com/] for more details"
            send_admin_email(subject="URGENT: Role error",
                                       recipients=RoleManager.roles_email_receivers,
                                       text=message)
            return {"error": f"Error in stripe webhook validating role: {e}"}, 409


    def get(self, user_id):

        try:
            timestamp =request.args['datetime']
        except KeyError as e:
            log_error(f"Error getting roles : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400


        try:
            role_manager = RoleManager()
            current_roles = role_manager.check_user_active_roles(user_id)
            purchasable_products = role_manager.get_purchasable_products(user_id)

            return {
                "purchasable_products": purchasable_products,
                "current_purchases": current_roles,
                "last_expired_purchase": role_manager.get_last_expired_roles(user_id),
            }, 200

        except Exception as e:
            log_error(f"Error getting roles : {e}")
            return {"error": f"Error getting roles : {e}"}, 400











