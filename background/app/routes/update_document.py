from flask import request
from flask_restful import Resource
from mojodex_core.db import with_db_session
from mojodex_core.documents.website_parser import WebsiteParser
from mojodex_core.entities.db_base_entities import MdUser
from app import db

from app import executor
from mojodex_core.entities.document import Document
from mojodex_core.logging_handler import log_error


class UpdateDocument(Resource):

    def post(self):
        try:
            timestamp = request.json['datetime']
            document_pk = request.json['document_pk']
            new_value = request.json["edition"] if "edition" in request.json else None
            user_id = request.json["user_id"]
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            document: Document = db.session.query(Document) \
                .join(MdUser, MdUser.user_id == Document.author_user_id) \
                .filter(Document.document_pk == document_pk) \
                .filter(MdUser.user_id == user_id) \
                .first()
            if document is None:
                return {"error": "Document not found for this user"}, 404

            @with_db_session
            def simple_doc_update(document_pk, new_value, db_session):
                try:
                    document: Document = db_session.query(Document).filter(Document.document_pk == document_pk).first()
                    document.update(new_value)
                except Exception as e:
                    log_error(f"simple_doc_update : {e}", notify_admin=True)

            @with_db_session
            def website_doc_update(document_pk, db_session):
                try:
                    document: Document = db_session.query(Document).filter(Document.document_pk == document_pk).first()
                    WebsiteParser().update_webpage_document(document)
                except Exception as e:
                    log_error(f"website_doc_update : {e}", notify_admin=True)

            if document.document_type == "learned_by_mojo":
                executor.submit(simple_doc_update, document_pk, new_value)
            else:
                executor.submit(website_doc_update, document_pk)

            return {"success": "ok"}, 200
        except Exception as e:
            return {"error": f"Error updating document : {e}"}, 404

