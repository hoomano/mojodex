from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *


class Goal(Resource):
    general_backend_error_message = "Oops, something weird has happened. We'll help you by email!"

    def __init__(self):
        Goal.method_decorators = [authenticate()]

    def put(self, user_id):
        if not request.is_json:
            log_error(f"Error creating Goal : Request must be JSON", notify_admin=True)
            return {"error": Goal.general_backend_error_message}, 400

        goal = None
        try:
            timestamp = request.json["datetime"]
            goal = request.json["goal"]
        except KeyError as e:
            log_error(
                f"Error creating Goal for user {user_id} - goal: {goal}: Missing field {e} - request.json: {request.json}",
                notify_admin=True)
            return {"error": Goal.general_backend_error_message}, 400

        try:
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
            user.goal = goal
            db.session.commit()
            return {"success": "Goal updated"}, 200
        except Exception as e:
            log_error(f"Error creating Goal for user {user_id} - request.json: {request.json} : {e}",
                      notify_admin=True)
            return {"error": Goal.general_backend_error_message}, 400


