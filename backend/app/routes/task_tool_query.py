import os
from datetime import datetime

from flask import request
from flask_restful import Resource
from app import db, log_error
from mojodex_core.entities import *


class TaskToolQuery(Resource):


    # adding new task tool query
    def put(self):
        if not request.is_json:
            return {"error": "Invalid request"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"Error creating new task_tool_query: Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error creating new task_tool_query: Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.json["datetime"]
            query = request.json["query"]
            task_tool_execution_fk = request.json["task_tool_execution_fk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            task_tool_execution = db.session.query(MdTaskToolExecution).filter(MdTaskToolExecution.task_tool_execution_pk == task_tool_execution_fk).first()
            if not task_tool_execution:
                return {"error": f"Task tool execution not found"}, 400

            # create task_tool_query
            task_tool_query = MdTaskToolQuery(
                task_tool_execution_fk=task_tool_execution_fk,
                query=query
            )

            db.session.add(task_tool_query)
            db.session.commit()
            return {"task_tool_query_pk": task_tool_query.task_tool_query_pk}, 200
        except Exception as e:
            log_error(f"Error creating new task_tool_query: {e}")
            return {"error": f"Error creating new task_tool_query: {e}"}, 500


    # editing new task tool query
    def post(self):
        if not request.is_json:
            return {"error": "Invalid request"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"Error editing task_tool_query: Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error editing task_tool_query: Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.json["datetime"]
            result = request.json["result"]
            task_tool_query_pk = request.json["task_tool_query_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            task_tool_query = db.session.query(MdTaskToolQuery).filter(MdTaskToolQuery.task_tool_query_pk == task_tool_query_pk).first()
            if not task_tool_query:
                return {"error": f"Task tool query not found"}, 400

            # create task_tool_query
            task_tool_query.result_date = datetime.now()
            task_tool_query.result = result

            db.session.commit()
            return {"task_tool_query_pk": task_tool_query.task_tool_query_pk}, 200
        except Exception as e:
            log_error(f"Error creating new task_tool_query: {e}")
            return {"error": f"Error creating new task_tool_query: {e}"}, 500