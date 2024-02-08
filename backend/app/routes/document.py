import os
from datetime import datetime
from flask import request
from flask_restful import Resource
from app import db, log_error
from db_models import *
class Document(Resource):

    def put(self):

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"Error creating document : Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error creating document : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        if not request.is_json:
            return {"error": "Request must be in json format"}, 400

        try:
            timestamp = request.json["datetime"]
            name = request.json["name"]
            document_type = request.json["document_type"]
            user_id = request.json["user_id"]
        except KeyError as e:
            return {"error": f"Missing key {e} in json"}, 400

        try:
            document = MdDocument(
                name=name,
                author_user_id=user_id,
                document_type=document_type,
                creation_date=datetime.now(),
            )
            db.session.add(document)
            db.session.commit()
            db.session.refresh(document)

            return {"document_pk": document.document_pk}, 200
        except Exception as e:
            log_error(f"Error creating document : {e}")
            return {"error": f"Error creating document : {e}"}, 500

    def post(self):

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"Error updating tool_execution : Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error updating tool_execution  : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        if not request.is_json:
            return {"error": "Request must be in json format"}, 400

        try:
            timestamp = request.json["datetime"]
            document_pk = request.json["document_pk"]
            update_date = request.json["update_date"]
        except KeyError as e:
            return {"error": f"Missing key {e} in json"}, 400

        try:
            document = db.session.query(MdDocument).filter(MdDocument.document_pk == document_pk).first()
            if not document:
                return {"error": "Document not found"}, 404

            document.last_update_date = update_date
            db.session.commit()
            return {"document_pk": document.document_pk}, 200
        except Exception as e:
            log_error(f"Error updating document  : {e}")
            return {"error": f"Error updating document  : {e}"}, 500




