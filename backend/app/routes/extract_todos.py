import os

from operator import and_

import requests
from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *
from sqlalchemy import func, desc
from datetime import datetime, timedelta

class ExtractTodos(Resource):

    def post(self):
        if not request.is_json:
            log_error(f"Error running extract todos : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_SCHEDULER_SECRET"]:
                log_error(f"Error running extract todos : Authentication error : Wrong secret", notify_admin=True)
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error running extract todos : Missing Authorization secret in headers", notify_admin=True)
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.json['datetime']
        except KeyError:
            log_error(f"Error running extract todos : Missing datetime in body", notify_admin=True)
            return {"error": f"Missing datetime in body"}, 400

        try:

            # find all the user_task_execution_pks that are ready for followup suggestion
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
                    .filter(MdUserTaskExecution.todos_extracted.is_(None))
                    .order_by(MdUserTaskExecution.user_task_execution_pk)
                    .limit(n_user_task_executions)
                    .offset(offset)
                    .all()
                )

                user_task_execution_pks+=[user_task_execution_pk[0] for user_task_execution_pk in results]
                offset += n_user_task_executions

            def extract_todos_background(user_task_execution_pk):
                # call background backend /extract_todos
                uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/extract_todos"
                pload = {"datetime": datetime.now().isoformat(), "user_task_execution_pk": user_task_execution_pk}
                internal_request = requests.post(uri, json=pload)
                if internal_request.status_code != 200:
                    log_error(f"Error while calling background extract_todos : {internal_request.text}")
                    # We won't return an error to the user, because the task has been ended but the background process failed


            for user_task_execution_pk in user_task_execution_pks:
                extract_todos_background(user_task_execution_pk)

            return {"user_task_execution_pks": user_task_execution_pks}, 200

        except Exception as e:
            log_error(f"Error running extract todos : {e}", notify_admin=True)
            return {"error": f"Error running extract todos : {e}"}, 500


    # mark todo as extracted
    def put(self):
        log_message = "Error marking todo as extracted"
        if not request.is_json:
            return {"error": "Invalid request"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"{log_message}: Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"{log_message}: Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.json["datetime"]
            user_task_execution_fk = request.json["user_task_execution_fk"]
        except KeyError as e:
            log_error(f"{log_message}: Missing key in body: {e}")
            return {"error": f"Missing key in body : {e}"}, 400

        try:
            user_task_execution = db.session.query(MdUserTaskExecution).filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_fk).first()
            if not user_task_execution:
                log_error(f"{log_message}: user_task_execution not found")
                return {"error": f"user_task_execution not found"}, 404

            user_task_execution.todos_extracted = datetime.now()
            db.session.commit()
            return {"user_task_execution_pk": user_task_execution_fk}, 200
        except Exception as e:
            log_error(f"{log_message}: {e}")
            return {"error": f"{log_message}: {e}"}, 500



