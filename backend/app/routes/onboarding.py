from flask import request
from flask_restful import Resource
from app import db, authenticate, log_error
from db_models import *
from datetime import datetime


class Onboarding(Resource):

    def __init__(self):
        Onboarding.method_decorators = [authenticate()]

    def put(self, user_id):
        if not request.is_json:
            log_error(f"Error setting onboarding presented date : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
        except KeyError as e:
            log_error(f"Error setting onboarding presented date : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()

            if user is None:
                db.session.rollback()
                log_error(f"Error setting onboarding presented date : User with user_id {user_id} does not exist")
                return {"error": f"Invalid user user_id: {user_id}"}, 400

            user.onboarding_presented = datetime.now()
            db.session.flush()

            db.session.commit()
            return {"user_id": user_id}, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"Error setting onboarding presented date : {e}")
            return {"error": f"Error setting onboarding presented date: {e}"}, 400


    def get(self, user_id):
        # data
        try:
            timestamp = request.args["datetime"]
        except KeyError as e:
            log_error(f"Error asking for onboarding presented : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
            if user is None:
                db.session.rollback()
                log_error(f"Error asking for onboarding presented : User with user_id {user_id} does not exist")
                return {"error": f"Invalid user user_id: {user_id}"}, 400

            return {"onboarding_presented": user.onboarding_presented is not None}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error asking for onboarding presented : {e}")
            return {"error": f"Error asking for onboarding presented : {e}"}, 400