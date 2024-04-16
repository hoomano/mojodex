import os

import pytz
from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *

from models.role_manager import RoleManager
from datetime import datetime

from sqlalchemy import func, text

from mojodex_core.mail import send_admin_email


class ExpiredRolesChecker(Resource):

    # checking for expired roles
    def post(self):
        error_message = "Error checking for expired roles"
        if not request.is_json:
            log_error(f"{error_message} : Request must be JSON", notify_admin=True)
            return {"error": "Invalid request"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_SCHEDULER_SECRET"]:
                log_error(f"{error_message} : Authentication error : Wrong secret", notify_admin=True)
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"{error_message} : Missing Authorization secret in headers", notify_admin=True)
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.json['datetime']
            n_roles = min(50, int(request.args["n_purchases"])) if "n_purchases" in request.args else 50
        except KeyError:
            log_error(f"{error_message} : Missing datetime in body", notify_admin=True)
            return {"error": f"Missing datetime in body"}, 400

        try:
            # Find all active roles with < 0 number of remaining days on products that are limited in time
            # Get current time with timezone
            utc = pytz.UTC
            current_time = datetime.now(utc)

            result = db.session.query(MdRole, MdUser)\
                .join(MdProfile, MdProfile.product_pk == MdRole.product_fk) \
                .join(MdUser, MdUser.user_id == MdRole.user_id) \
                .filter(MdRole.active == True) \
                .filter(MdProfile.n_days_validity.isnot(None)) \
                .filter(current_time - func.date(MdRole.creation_date) > text(
                f'md_product.n_days_validity * interval \'1 day\'')) \
                .limit(n_roles) \
                .all()

            if result is None:
                return {"purchase_pks": []}, 200

            for expired_active_role, user in result:
                role_manager = RoleManager()
                role_manager.deactivate_role(expired_active_role)
                try:
                    message = f"Role {expired_active_role.role_pk} of user user_id: {user.user_id} email: {user.email} " \
                              f"has been deactivated because its validity period has expired"
                    send_admin_email(subject="🚨 A role has expired",
                                     recipients=RoleManager.roles_email_receivers,
                                     text=message)
                except Exception as e:
                    log_error(f"Error sending mail : {e}")

            db.session.commit()

            return {"purchase_pks": [role.role_pk for role, user in result]}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} request.json: {request.json}: {e}", notify_admin=True)
            return {"error": f"{error_message} : {e}"}, 400




