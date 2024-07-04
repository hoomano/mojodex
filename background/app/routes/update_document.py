from flask import request
from flask_restful import Resource
from mojodex_core.entities.db_base_entities import *
from app import db, document_manager
from models.documents.website_parser import WebsiteParser

from app import executor
from mojodex_core.logging_handler import log_error


class UpdateDocument(Resource):

    def __init__(self):
        self.website_parser = WebsiteParser()

    def post(self):
        try:
            timestamp = request.json['datetime']
            document_pk = request.json['document_pk']
            edition = request.json["edition"]
            user_id = request.json["user_id"]
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            document = db.session.query(MdDocument) \
                .join(MdUser, MdUser.user_id == MdDocument.author_user_id) \
                .filter(MdDocument.document_pk == document_pk) \
                .filter(MdUser.user_id == user_id) \
                .first()
            if document is None:
                return {"error": "Document not found for this user"}, 404

            company_name = db.session.query(MdCompany.name) \
                .join(MdUser, MdUser.company_fk == MdCompany.company_pk) \
                .filter(MdUser.user_id == user_id) \
                .first()[0]

            document_chunks_pks = db.session.query(MdDocumentChunk.document_chunk_pk).filter(
                MdDocumentChunk.document_fk == document_pk)\
                .filter(MdDocumentChunk.deleted.is_(None))\
                .all()
            document_chunks_pks = [document_chunk_pk[0] for document_chunk_pk in document_chunks_pks]

            def launch_document_update(document_name, document_type, document_manager_app, user_id, edition, document_chunks_pks, company_name, website_parser):
                try:
                    if document_type == "learned_by_mojo":
                        document_manager_app.update_document(user_id, document_pk, document_chunks_pks, edition)
                    elif document_type == "webpage":
                        website_parser.update_website_document( user_id, document_name, document_pk, document_chunks_pks, company_name)
                except Exception as e:
                    log_error(f"launch_document_update : {e}", notify_admin=True)

            executor.submit(launch_document_update, document.name, document.document_type, document_manager, user_id, edition, document_chunks_pks, company_name, self.website_parser)

            return {"success": "ok"}, 200
        except Exception as e:
            return {"error": f"Error updating document : {e}"}, 404

