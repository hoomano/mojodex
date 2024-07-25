from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.authentication import authenticate
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *
import json
import os


class Language(Resource):
    languages_dir = "mojodex_core/languages"
    available_languages_file = "available_languages.json"
    general_backend_error_message = "Oops, something weird has happened. We'll help you by email!"

    def __init__(self):
        Language.method_decorators = [authenticate(methods=["POST"])]

    # Set the language of the user
    def post(self, user_id):
        if not request.is_json:
            log_error(f"Error updating language : Request must be JSON", notify_admin=True)
            return {"error": Language.general_backend_error_message}, 400

        language_code = None
        try:
            timestamp = request.json["datetime"]
            language_code = request.json["language_code"]
        except KeyError as e:
            log_error(
                f"Error updating language for user {user_id} - language_code: {language_code}: Missing field {e} - request.json: {request.json}",
                notify_admin=True)
            return {"error": Language.general_backend_error_message}, 400

        try:
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()

            if user is None:
                log_error(f"Error updating language for user {user_id} - language_code: {language_code}: User not found", notify_admin=True)
                return {"error": Language.general_backend_error_message}, 400

            user.language_code = language_code
            db.session.commit()
            return {"success": "Language updated"}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error updating language for user {user_id} - request.json: {request.json} : {e}",
                      notify_admin=True)
            return {"error": Language.general_backend_error_message}, 400

    # Get the system language of the user
    # This route is unprotected because it is used to get the language of the system without being logged in
    # Always returns english as default system language
    def get(self):
        try:
            timestamp = request.args["datetime"]
            language_code = request.args["language_code"]
        except KeyError as e:
            log_error(f"Error getting language : Missing field {e}")
            return {"error": Language.general_backend_error_message}, 400

        try:
            # Return all available languages
            with open(os.path.join(self.languages_dir, self.available_languages_file), "r") as f:
                available_languages = json.load(f)

            # If the language requested is not in the available languages, return the english as default
            if language_code not in available_languages: language_code = "en"

            language_path_file = os.path.join(self.languages_dir, f"{language_code}.json")
            with open(language_path_file, "r") as f:
                language_json_file = json.load(f)

            return {
                "available_languages": available_languages,
                "language_json_file": language_json_file}, 200

        except Exception as e:
            log_error(f"Error getting language : {e}")
            return {"error": Language.general_backend_error_message}, 400

