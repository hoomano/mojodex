import os
from datetime import datetime

from flask import request
from flask_restful import Resource
from app import db, log_error
from db_models import *


class UserPreference(Resource):

    def post(self):
        error_message = "Error saving user_preference"

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"{error_message} : Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"{error_message}  : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        if not request.is_json:
            return {"error": "Request must be in json format"}, 400

        try:
            timestamp = request.json["datetime"]
            tag_label = request.json["tag"]
            user_id = request.json["user_id"]
            description = request.json["user_preference"]
        except KeyError as e:
            return {"error": f"Missing key {e} in json"}, 400

        try:
            tag = db.session.query(MdTag).filter(MdTag.label == tag_label).first()
            if not tag:
                return {"error": f"Tag {tag_label} not found"}, 404

            user_preference = db.session.query(MdUserPreference) \
                .filter(MdUserPreference.user_id == user_id) \
                .filter(MdUserPreference.tag_fk == tag.tag_pk) \
                .first()

            if not user_preference:
                # create new user_preference
                user_preference = MdUserPreference(user_id=user_id, tag_fk=tag.tag_pk, description=description)
                db.session.add(user_preference)
            else:
                # update existing user_preference
                user_preference.description = description
                user_preference.last_update_date = datetime.now()
            db.session.commit()
            return {"user_preference_pk": user_preference.user_preference_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message}  : {e}")
            return {"error": f"{error_message}  : {e}"}, 500

    def get(self):
        error_message = "Error getting user_preference"

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"{error_message} : Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"{error_message}  : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.args["datetime"]
            tag_label = request.args["tag"]
            user_id = request.args["user_id"]
        except KeyError as e:
            return {"error": f"Missing key {e} in json"}, 400

        try:
            tag = db.session.query(MdTag).filter(MdTag.label == tag_label).first()
            if not tag:
                return {"error": f"Tag {tag_label} not found"}, 404

            user_preference = db.session.query(MdUserPreference) \
                .filter(MdUserPreference.user_id == user_id) \
                .filter(MdUserPreference.tag_fk == tag.tag_pk) \
                .first()

            return {"user_preference": user_preference.description if user_preference else ""}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message}  : {e}")
            return {"error": f"{error_message}  : {e}"}, 500
