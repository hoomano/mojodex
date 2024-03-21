from flask import request
from flask_restful import Resource
from app import authenticate
from mojodex_core.logging_handler import log_error


class Error(Resource):

    def __init__(self):
        Error.method_decorators = [authenticate()]

    def put(self, user_id):
        if not request.is_json:
            log_error(f"Error sending error : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            error = request.json["error"]
            notify_admin = request.json["notify_admin"] if "notify_admin" in request.json else False
        except KeyError as e:
            log_error(f"Error sending error : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            if notify_admin:
                error+=f"\nUser: {user_id}"
            log_error(error, session_id=request.json["session_id"] if "session_id" in request.json else None, notify_admin=notify_admin)

            return {"success": "Error logged"}, 200
        except Exception as e:
            log_error(f"Error sending error : {e}")
            return {"error": f"Error sending error : {e}"}, 400