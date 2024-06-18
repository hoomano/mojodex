import os
from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *

class UserSummary(Resource):

    # updating user_summary
    def post(self):
        if not request.is_json:
            return {"error": "Invalid request"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"Error updating user summary : Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error updating user summary : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.json["datetime"]
            summary = request.json["summary"]
            session_id = request.json["session_id"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            # find user associated to session
            user = db.session.query(MdUser)\
                .join(MdSession, MdUser.user_id == MdSession.user_id)\
                .filter(MdSession.session_id == session_id)\
                .first()
            if user is None:
                return {"error": f"Invalid session_id: {session_id}"}, 400

            # update user summary
            user.summary = summary
            db.session.commit()

            return {"success": True}, 200
        except Exception as e:
            log_error(f"Error updating user summary : {e}")
            return {"error": f"Error updating user summary : {e}"}, 400