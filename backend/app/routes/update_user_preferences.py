import os
from datetime import datetime, timedelta
from operator import and_

import requests
from flask import request
from flask_restful import Resource
from app import db, log_error, server_socket
from db_models import *
from sqlalchemy import func, desc


class UpdateUserPreferences(Resource):

    def post(self):
        error_message = "Error selecting user_task_execution for update user preferences"

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_SCHEDULER_SECRET"]:
                log_error(f"{error_message}: Authentication error : Wrong secret", notify_admin=True)
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"{error_message}: Missing Authorization secret in headers", notify_admin=True)
            return {"error": f"Missing Authorization secret in headers"}, 403

        if not request.is_json:
            log_error(f"{error_message}: Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        try:
            timestamp = request.json['datetime']
        except KeyError:
            log_error(f"{error_message}: Missing datetime in body", notify_admin=True)
            return {"error": f"Missing datetime in body"}, 400

        try:
            if os.environ['ENVIRONMENT'] != 'prod':
                return {"user_task_execution_pks": []}, 200

            # find all the user_task_execution_pks that are ready for updating user preferences
            now = datetime.now()
            time_20_min_ago = now - timedelta(minutes=20)
            time_10_min_ago = now - timedelta(minutes=10)

            offset = 0
            n_user_task_executions = 50
            user_task_execution_pks = []
            results = []

            while len(results) == 50 or offset == 0:
                # Subquery to find last associated produced text version's date
                last_produced_text_version_subquery = db.session.query(MdProducedText.user_task_execution_fk.label('user_task_execution_fk'),
                                                  MdProducedTextVersion.creation_date.label('creation_date'),
                                                  func.row_number().over(
                                                      partition_by=MdProducedText.user_task_execution_fk,
                                                      order_by=desc(MdProducedTextVersion.creation_date),
                                                  ).label("row_number")) \
                    .join(MdProducedTextVersion, MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk) \
                    .subquery()

                results = (
                    db.session.query(MdUserTaskExecution.user_task_execution_pk)
                    .join(last_produced_text_version_subquery, and_(
                        last_produced_text_version_subquery.c.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk,
                        last_produced_text_version_subquery.c.row_number == 1))
                    .filter(
                        and_(
                            last_produced_text_version_subquery.c.creation_date > time_20_min_ago,
                            last_produced_text_version_subquery.c.creation_date <= time_10_min_ago
                        )
                    )
                    .order_by(MdUserTaskExecution.user_task_execution_pk)
                    .limit(n_user_task_executions)
                    .offset(offset)
                    .all()
                )

                user_task_execution_pks+=[user_task_execution_pk[0] for user_task_execution_pk in results]
                offset += n_user_task_executions

            def update_user_preferences_background(user_task_execution_pk):
                # call background backend /update_user_preferences
                uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/update_user_preferences"
                pload = {"datetime": datetime.now().isoformat(), "user_task_execution_pk": user_task_execution_pk}
                internal_request = requests.post(uri, json=pload)
                if internal_request.status_code != 200:
                    log_error(f"Error while calling background update_user_preferences : {internal_request.text}")
                    # We won't return an error to the user, because the task has been ended but the background process failed


            for user_task_execution_pk in user_task_execution_pks:
                update_user_preferences_background(user_task_execution_pk)

            return {"user_task_execution_pks": user_task_execution_pks}, 200

        except Exception as e:
            log_error(f"{error_message} : {e}", notify_admin=True)
            return {"error": f"{error_message} : {e}"}, 500




