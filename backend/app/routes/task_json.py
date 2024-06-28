import os

from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import MdTextType

from mojodex_core.llm_engine.mpt import MPT
from mojodex_core.json_loader import json_decode_retry
from mojodex_core.logging_handler import on_json_error
from datetime import datetime


class TaskJson(Resource):

    task_json_mpt_filename = "instructions/generate_task_json.mpt"

    def __get_text_types(self):
        try:
            text_types = db.session.query(MdTextType.name).all()
            return [text_type.name for text_type in text_types]
        except Exception as e:
            raise Exception(f"__get_text_types : {str(e)}")

    @json_decode_retry(retries=3, required_keys=[], on_json_error=on_json_error)
    def __generate_task_json(self, task_requirements, existing_text_types):
        try:
            generate_task_mpt = MPT(
                self.task_json_mpt_filename, task_requirements=task_requirements, existing_text_types=existing_text_types)

            responses = generate_task_mpt.run(
                user_id="backoffice", temperature=0, max_tokens=4000, json_format=True)

            response = responses[0]
            return response
        except Exception as e:
            raise Exception(f"__generate_task_json : {str(e)}")

    # Route to create a new task json
    # Route used only by Backoffice
    # Protected by a secret
    def post(self):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["BACKOFFICE_SECRET"]:
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(
                f"Error creating new task : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.json["datetime"]
            task_requirements = request.json["task_requirements"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            existing_text_types = self.__get_text_types()
            task_json = self.__generate_task_json(
                task_requirements, existing_text_types)
            task_json["datetime"] = datetime.now().isoformat()
            # TODO: Predefined actions are not in the prompt while not documented
            task_json["predefined_actions"] = []
            return task_json, 200
        except Exception as e:
            log_error(f"Error creating new task : {str(e)}")
            return {"error": f"Error creating new task : {str(e)}"}, 500
