import os
from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.authentication import authenticate_with_backoffice_secret
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *

class TextType(Resource):


    def __init__(self):
        TextType.method_decorators = [authenticate_with_backoffice_secret(methods=["PUT", "POST", "GET"])]

    # Route to create a new text_type
    # Route used only by Backoffice
    # Protected by a secret
    def put(self):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400

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

    def post(self):
        
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400

        try:
            timestamp = request.json["datetime"]
            text_type_pk = request.json["text_type_pk"]
            text_edit_action_pk = request.json["text_edit_action_pk"]
        except KeyError as e:
            return {"error": f"Missing field: {e}"}, 400
        
        try:
            # check text type exists
            text_type = db.session.query(MdTextType).filter(MdTextType.text_type_pk == text_type_pk).first()
            if text_type is None:
                return {"error": f"Text type {text_type_pk} does not exist"}, 400
            
            # check text edit action exists
            text_edit_action = db.session.query(MdTextEditAction).filter(MdTextEditAction.text_edit_action_pk == text_edit_action_pk).first()
            if text_edit_action is None:
                return {"error": f"Text edit action {text_edit_action_pk} does not exist"}, 400
            
            # check association does not already exist
            association = db.session.query(MdTextEditActionTextTypeAssociation).filter(MdTextEditActionTextTypeAssociation.text_type_fk == text_type_pk, MdTextEditActionTextTypeAssociation.text_edit_action_fk == text_edit_action_pk).first()
            if association is not None:
                return {"error": f"Association between text type {text_type_pk} and text edit action {text_edit_action_pk} already exists"}, 400
            
            # create association
            association = MdTextEditActionTextTypeAssociation(text_type_fk=text_type_pk, text_edit_action_fk=text_edit_action_pk)
            db.session.add(association)
            db.session.commit()

            return {"text_edit_action_text_type_association_pk": association.text_edit_action_text_type_association_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error associating text_type with text_edit_action: {e}")
            return {"error": f"Error associating text_type with text_edit_action : {e}"}, 400