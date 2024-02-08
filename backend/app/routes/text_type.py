import os
from flask import request
from flask_restful import Resource
from app import db, log_error
from db_models import *

class TextType(Resource):

    # Route to create a new text_type
    # Route used only by Backoffice
    # Protected by a secret
    def put(self):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["BACKOFFICE_SECRET"]:
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error creating new text_type : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.json["timestamp"]
            text_type_name = request.json["text_type_name"]
        except KeyError as e:
            return {"error": f"Missing field: {e}"}, 400

        try:
            # check text type name is not already used
            text_type = db.session.query(MdTextType).filter(MdTextType.name == text_type_name).first()
            if text_type is not None:
                return {"error": f"Text type name {text_type_name} already exists"}, 400

            # create new text type
            text_type = MdTextType(name=text_type_name)
            db.session.add(text_type)
            db.session.commit()
            db.session.refresh(text_type)

            return {"text_type_pk": text_type.text_type_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error creating new text_type : {e}")
            return {"error": f"Error creating new text_type : {e}"}, 400

    # get list of existing text types
    def get(self):
        try:
            secret = request.headers['Authorization']
            if secret != os.environ["BACKOFFICE_SECRET"]:
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error creating new text_type : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.args["datetime"]
            n_text_types = min(int(request.args["n_text_types"]), 50) if "n_text_types" in request.args else 50
            offset = int(request.args["offset"]) if "offset" in request.args else 0
        except KeyError as e:
            return {"error": f"Missing field: {e}"}, 400

        try:
            text_types = db.session.query(MdTextType).order_by(MdTextType.text_type_pk).limit(n_text_types).offset(offset).all()
            text_types = [{"text_type_pk": text_type.text_type_pk, "name": text_type.name} for text_type in text_types]
            return {"text_types": text_types}, 200
        except Exception as e:
            log_error(f"Error getting text_types : {e}")
            return {"error": f"Error getting text_types : {e}"}, 400
