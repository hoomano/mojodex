from flask import request
from flask_restful import Resource
from app import db, authenticate, log_error, executor
from mojodex_core.entities import *


class Timezone(Resource):
    general_backend_error_message = "Oops, something weird has happened. We'll help you by email!"

    def __init__(self):
        Timezone.method_decorators = [authenticate()]

    def post(self, user_id):
        if not request.is_json:
            log_error(f"Error updating timezone : Request must be JSON", notify_admin=True)
            return {"error": Timezone.general_backend_error_message}, 400

        timezone_offset = None
        try:
            timestamp = request.json["datetime"]
            timezone_offset = request.json["timezone_offset"]
        except KeyError as e:
            log_error(
                f"Error updating timezone_offset for user {user_id} - timezone_offset: {timezone_offset}: Missing field {e} - request.json: {request.json}",
                notify_admin=True)
            return {"error": Timezone.general_backend_error_message}, 400

        try:
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
            if user is None:
                log_error(f"Error updating timezone_offset for user {user_id} - timezone_offset: {timezone_offset}: User not found", notify_admin=True)
                return {"error": Timezone.general_backend_error_message}, 400

            user.timezone_offset = timezone_offset
            db.session.commit()
            return {"success": "Timezone updated"}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error updating timezone_offset for user {user_id} - request.json: {request.json} : {e}",
                      notify_admin=True)
            return {"error": Timezone.general_backend_error_message}, 400

