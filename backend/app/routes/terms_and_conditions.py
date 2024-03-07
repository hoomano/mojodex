from flask import request
from flask_restful import Resource
from jinja2 import Template
from models.session.session import Session as SessionModel
from app import db, authenticate, log_error
from mojodex_core.entities import *
from datetime import datetime



class TermsAndConditions(Resource):

    def __init__(self):
        TermsAndConditions.method_decorators = [authenticate()]

    def put(self, user_id):
        if not request.is_json:
            log_error(f"Error adding terms and conditions agreement : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
        except KeyError as e:
            log_error(f"Error adding terms and conditions agreement : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
            if user is None:
                db.session.rollback()
                log_error(f"Error adding terms and conditions agreement : User with user_id {user_id} does not exist")
                return {"error": f"Invalid user user_id: {user_id}"}, 400

            user.terms_and_conditions_accepted = timestamp
            db.session.commit()
            return {"success": True}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error adding terms and conditions agreement : {e}")
            return {"error": f"{e}"}, 400