import os
from datetime import datetime

from flask import request
from flask_restful import Resource
from app import db, log_error
from mojodex_core.entities import MdTextType

from jinja2 import Template
from mojodex_core.json_loader import json_decode_retry
from app import on_json_error

from app import llm, llm_conf, llm_backup_conf


class TaskJson(Resource):

    task_json_prompt = "/data/prompts/tasks/generate_json.txt"
    task_json_generator = llm(
        llm_conf, label="GENERATE_TASK_JSON", llm_backup_conf=llm_backup_conf)

    def __get_text_types(self):
        try:
            text_types = db.session.query(MdTextType.name).all()
            return [text_type.name for text_type in text_types]
        except Exception as e:
            raise Exception(f"__get_text_types : {str(e)}")

    @json_decode_retry(retries=3, required_keys=[], on_json_error=on_json_error)
    def __generate_task_json(self, task_requirements, existing_text_types):
        try:
            with open(self.task_json_prompt, "r") as f:
                template = Template(f.read())
                prompt = template.render(
                    task_requirements=task_requirements, existing_text_types=existing_text_types)

            messages = [{"role": "system", "content": prompt}]

            responses = self.task_json_generator.invoke(
                messages, "backoffice", temperature=0, max_tokens=4000, json_format=True)

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
