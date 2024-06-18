
import os
import stripe
from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.entities.db_base_entities import *
from mojodex_core.mail import send_admin_email
from mojodex_core.logging_handler import log_error

from mojodex_backend_logger import MojodexBackendLogger

from models.purchase_manager import PurchaseManager


class PurchaseEndStripeWebHook(Resource):
    logger_prefix = "PurchaseEndStripeWebHook:: "

    def __init__(self):
        self.logger = MojodexBackendLogger(
            f"{PurchaseEndStripeWebHook.logger_prefix}")

    def post(self):
        try:
            if not request.is_json:
                log_error(f"Error on stripe webhook end of purchase : Request must be JSON")
                return {"error": "Request must be JSON"}, 400
        except Exception as e:
            log_error(f"Error on stripe webhook end of purchase : Request must be JSON")
            return {"error": "Request must be JSON"}, 400


        try:
            signature = request.headers.get('stripe-signature')
            event = stripe.Webhook.construct_event(
                payload=request.data, sig_header=signature, secret=os.environ["STRIPE_WEBHOOK_SECRET_END_PURCHASE"])

            # Get the type of webhook event sent - used to check the status of PaymentIntents.
            event_type = event['type']

            if event_type not in ["customer.subscription.deleted", "customer.subscription.pending_update_expired"]:
                log_error('Unhandled event type %s', event_type)
                return {"error": f"Unhandled event type : {event_type}"}, 500

            data = event['data']
            subscription_id = data['object']['id']

            # find associated purchase in db:
            purchase = db.session.query(MdPurchase).filter(MdPurchase.subscription_stripe_id == subscription_id).first()
            if purchase is None:
                log_error(f"Purchase with subscription_stripe_id {subscription_id} does not exist in mojodex db")
                message = f"Subscription id {subscription_id} ended but associated purchase was not found in db"
                send_admin_email(subject="URGENT: Subscription end error",
                                           recipients=PurchaseManager.purchases_email_receivers,
                                           text=message)

                return {"error": f"Purchase with subscription_stripe_id {subscription_id} does not exist in mojodex db"}, 400

            # deactivate purchase
            purchase_manager = PurchaseManager()
            purchase_manager.deactivate_purchase(purchase)


            user_email = db.session.query(MdUser.email).filter(MdUser.user_id == purchase.user_id).first()[0]
            try:
                message = f"Subscription of user {user_email} ended"
                send_admin_email(subject="A client subscription ended",
                                           recipients=PurchaseManager.purchases_email_receivers,
                                           text=message)
            except Exception as e:
                log_error(f"Error sending mail : {e}")

            db.session.commit()
            return {"purchase_pk": purchase.purchase_pk}, 200

        except Exception as e:
            log_error(f"Error in stripe webhook ending purchase: {e}")
            message = f"A subscription end error occurred : {e}\n See [https://dashboard.stripe.com/] for more details"
            send_admin_email(subject="URGENT: End of subscription error",
                                       recipients=PurchaseManager.purchases_email_receivers,
                                       text=message)
            return {"error": f"Error in stripe webhook ending purchase: {e}"}, 409












