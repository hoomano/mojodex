
import os


from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.authentication import authenticate_with_scheduler_secret
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *
from sqlalchemy import func, text, and_

from mojodex_backend_logger import MojodexBackendLogger

from mojodex_core.email_sender.email_service import EmailService

from models.purchase_manager import PurchaseManager
from datetime import datetime, timedelta, timezone

class FreeUsersEngagementChecker(Resource):
    logger_prefix = "FreeUsersEngagementChecker::"

    def __init__(self):
        FreeUsersEngagementChecker.method_decorators = [authenticate_with_scheduler_secret(methods=["POST"])]



    def __init__(self):
        self.logger = MojodexBackendLogger(FreeUsersEngagementChecker.logger_prefix)

    def calculate_previous_working_day(self, input_date):
        # Define the number of working days to go back
        working_days_to_subtract = 2

        # Loop until we reach the desired number of working days
        while working_days_to_subtract > 0:
            # Subtract one day from the input date
            input_date -= timedelta(days=1)

            # Check if the resulting date is a weekday (Monday to Friday)
            if input_date.weekday() < 5:
                working_days_to_subtract -= 1

        return input_date

    def post(self):
        error_message = "Error checking free users engagement"
        if not request.is_json:
            log_error(f"{error_message} : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        try:
            timestamp = request.json['datetime']
            n_disengaged_users = min(50, int(request.json["n_disengaged_users"])) if "n_disengaged_users" in request.json else 50
            offset = int(request.json["offset"]) if "offset" in request.json else 0

        except KeyError:
            log_error(f"{error_message} : Missing datetime in body", notify_admin=True)
            return {"error": f"Missing datetime in body"}, 400

        try:

            # Calculate the date before 2 working days (we don't count today)
            # if today = monday, we check if user has done nothing thursday, friday and today
            today =datetime.now(timezone.utc).date() - timedelta(days=3)
            start_date_cutoff = self.calculate_previous_working_day(today)

            # Query for users with active free and limited products and MdUser.creation_date before the start_date_cutoff
            purchases_query = db.session.query(MdUser). \
                join(MdPurchase, MdUser.user_id == MdPurchase.user_id). \
                join(MdProduct, MdPurchase.product_fk == MdProduct.product_pk). \
                filter(and_(MdPurchase.active == True, MdProduct.free == True, MdProduct.n_days_validity.isnot(None),
                            MdUser.creation_date < start_date_cutoff))

            # Query for users with any user_task_execution within the last 2 working days
            working_days_query = db.session.query(MdUser) \
                .join(MdUserTask, MdUser.user_id == MdUserTask.user_id) \
                .join(MdUserTaskExecution, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk) \
                .filter((func.timezone(text(f'md_user.timezone_offset * interval \'1 minute\''),
                                       MdUserTaskExecution.start_date) >= start_date_cutoff))

            # Combine queries to get users with active free limited products and no recent user_task_execution
            # `except_` in SQLAlchemy is used to filter the results from the first query by excluding the results that are also present in the second query
            result_query = purchases_query.except_(working_days_query)

            # Execute the query and fetch the results
            users = result_query.limit(n_disengaged_users).offset(offset).all()

            # send email to admin
            for user in users:
                try:
                    message = f"User {user.user_id} - {user.email} currently in free trial is disengaged => They have done nothing in the last 2 working days (and nothing yet today)"
                    EmailService().end(subject="Disengaged free trial user",
                                     recipients=PurchaseManager.purchases_email_receivers,
                                     text=message)
                except Exception as e:
                    log_error(f"Error sending mail : {e}")

            # return list of user_ids
            return {"user_ids": [user.user_id for user in users]}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error sending daily emails : {e}", notify_admin=True)
            return {"error": f"Error sending daily emails : {e}"}, 500
