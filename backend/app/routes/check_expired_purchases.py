import os

import pytz
from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.authentication import authenticate_with_scheduler_secret
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *

from models.purchase_manager import PurchaseManager


from sqlalchemy import func, text

from mojodex_core.email_sender.email_service import EmailService
from datetime import datetime

class ExpiredPurchasesChecker(Resource):

    def __init__(self):
        ExpiredPurchasesChecker.method_decorators = [authenticate_with_scheduler_secret(methods=["POST"])]

    # checking for expired purchases
    def post(self):
        error_message = "Error checking for expired purchases"
        if not request.is_json:
            log_error(f"{error_message} : Request must be JSON", notify_admin=True)
            return {"error": "Invalid request"}, 400

        try:
            timestamp = request.json['datetime']
            n_purchases = min(50, int(request.args["n_purchases"])) if "n_purchases" in request.args else 50
        except KeyError:
            log_error(f"{error_message} : Missing datetime in body", notify_admin=True)
            return {"error": f"Missing datetime in body"}, 400

        try:
            # Find all active purchases with < 0 number of remaining days on products that are limited in time
            # Get current time with timezone
            utc = pytz.UTC
            current_time = datetime.now(utc)

            result = db.session.query(MdPurchase, MdUser)\
                .join(MdProduct, MdProduct.product_pk == MdPurchase.product_fk) \
                .join(MdUser, MdUser.user_id == MdPurchase.user_id) \
                .filter(MdPurchase.active == True) \
                .filter(MdProduct.n_days_validity.isnot(None)) \
                .filter(current_time - func.date(MdPurchase.creation_date) > text(
                f'md_product.n_days_validity * interval \'1 day\'')) \
                .limit(n_purchases) \
                .all()

            if result is None:
                return {"purchase_pks": []}, 200

            for expired_active_purchase, user in result:
                purchase_manager = PurchaseManager()
                purchase_manager.deactivate_purchase(expired_active_purchase)
                try:
                    message = f"Purchase {expired_active_purchase.purchase_pk} of user user_id: {user.user_id} email: {user.email} " \
                              f"has been deactivated because its validity period has expired"
                    EmailService().send(subject="🚨 A purchase has expired",
                                     recipients=PurchaseManager.purchases_email_receivers,
                                     text=message)
                except Exception as e:
                    log_error(f"Error sending mail : {e}")

            db.session.commit()

            return {"purchase_pks": [purchase.purchase_pk for purchase, user in result]}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} request.json: {request.json}: {e}", notify_admin=True)
            return {"error": f"{error_message} : {e}"}, 400




