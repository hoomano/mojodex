import os
import requests
from flask import request
from flask_restful import Resource
from app import db, translator
from mojodex_core.authentication import authenticate
from mojodex_core.documents.website_parser import WebsiteParser
from mojodex_core.entities.document import Document
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import MdCompany, MdUser
from typing import List, Dict, Any
from datetime import datetime

class MojoResource(Resource):


    def __init__(self):
        MojoResource.method_decorators = [authenticate()]



    def put(self, user_id):
        if not request.is_json:
            log_error(f"Error creating MojoResource : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            website_url = request.json["website_url"].lower()
        except KeyError as e:
            log_error(f"Error creating MojoResource : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        try:
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()

            try:
                website_url = WebsiteParser().check_url_validity(website_url)
                website_url = website_url[:-1] if website_url[-1] == "/" else website_url
            except Exception:
                return {"error": "invalid_url"}, 400

            # check website does not already exist for this user
            document: Document = db.session.query(Document) \
                .filter(Document.author_user_id == user_id) \
                .filter(Document.name == website_url) \
                .first()
            if document is not None:
                if document.deleted_by_user:  # If document exists but is deleted, undelete it and update it
                    document.deleted_by_user = False
                    db.session.commit()

                    # call background backend /update_document to update document
                    uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/update_document"
                    pload = {'datetime': datetime.now().isoformat(), 'document_pk': document.document_pk, "user_id": user_id, "edition": None}
                    internal_request = requests.post(uri, json=pload)
                    if internal_request.status_code != 200:
                        log_error(f"Error while calling background update_document : {internal_request.json()}")
                    return {"success": "ok"}, 200

                return {"error": "Website already exist in user's documents"}, 400


            # call background backend /create_document_from_website to create document from website
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/create_document_from_website"
            pload = {'datetime': datetime.now().isoformat(), 'website_url': website_url, "user_id": user_id}
            internal_request = requests.post(uri, json=pload)
            if internal_request.status_code != 200:
                log_error(f"Error while calling background create_document_from_website : {internal_request.json()}")

            return {"success": "ok"}, 200
        except Exception as e:
            log_error(f"Error creating MojoResource : {e}")
            db.session.rollback()
            return {"error": f"Error creating MojoResource : {e}"}, 500

    def post(self, user_id):
        if not request.is_json:
            log_error(f"Error updating MojoResource : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            document_pk = request.json["document_pk"]
        except KeyError as e:
            log_error(f"Error updating MojoResource : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        try:
            if document_pk == 'user_description':
                user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
                user.summary = translator.translate(request.json["edition"], user_id)
                user.last_summary_update_date = datetime.now()
                db.session.commit()
                return {"document_pk": document_pk}, 200

            if document_pk == 'company_description':
                user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
                user.company_description = translator.translate(request.json["edition"], user_id)
                user.last_company_description_update_date = datetime.now()
                db.session.commit()
                return {"document_pk": document_pk}, 200

            document: Document = db.session.query(Document) \
                .filter(Document.document_pk == document_pk) \
                .filter(Document.author_user_id == user_id) \
                .filter(Document.deleted_by_user == False) \
                .first()
            if document is None:
                return {"error": "Document not found for this user"}, 404

            edition = request.json["edition"] if document.document_type == "learned_by_mojo" else None

            # call background backend /update_document to update document
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/update_document"
            pload = {'datetime': datetime.now().isoformat(), 'document_pk': document_pk, "user_id": user_id, "edition": edition}
            internal_request = requests.post(uri, json=pload)
            if internal_request.status_code != 200:
                log_error(f"Error while calling background update_document : {internal_request.json()}")

            return {"document_pk": document_pk}, 200
        except Exception as e:
            log_error(f"Error updating MojoResource : {e}")
            db.session.rollback()
            return {"error": f"Error updating MojoResource : {e}"}, 500

    def get(self, user_id):

        try:
            timestamp = request.args["datetime"]
            learned_by_mojo = request.args["learned_by_mojo"].lower() == "true"
        except KeyError as e:
            log_error(f"Error getting messages : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        try:

            n_resources = min(50, int(request.args[
                                          "n_resources"])) if "n_resources" in request.args else 50
            offset = int(request.args["offset"]) if "offset" in request.args else 0
            result = db.session.query(Document, MdUser) \
                .join(MdUser, MdUser.user_id == Document.author_user_id) \
                .filter(Document.author_user_id == user_id) \
                .filter(Document.deleted_by_user == False)

            if learned_by_mojo:
                result = result.filter(Document.document_type == "learned_by_mojo")
            else:
                result = result.filter(Document.document_type != "learned_by_mojo")

            result = result.order_by(Document.creation_date.desc()) \
                .limit(n_resources) \
                .offset(offset) \
                .all()

            # list was provided a type because the ide type checker raised a false positive warning
            documents_list: List[Dict[str, Any]] = [{"document_pk": document.document_pk,
                               "document_type": document.document_type,
                               "name": document.name,
                               "author": author.name,
                               "creation_date": document.creation_date.isoformat(),
                               "last_update_date": document.last_update_date.isoformat() if document.last_update_date is not None else document.creation_date.isoformat(),
                               "text": document.text
                               } for document, author in result] if result is not None else []

            if learned_by_mojo:
                if offset == 0:
                    user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
                    if user.summary is not None:
                        documents_list.append({
                                                "document_pk":"user_description",
                                                "document_type": "learned_by_mojo",
                                                "name": f"{user.name} knowledge",
                                               "text": user.summary,
                                               "author": user.name,
                                                "creation_date": user.creation_date.isoformat(),
                                                "last_update_date": user.last_summary_update_date.isoformat() if user.last_summary_update_date is not None else user.creation_date.isoformat()
                        })
                    company_name = db.session.query(MdCompany.name).join(MdUser, MdUser.company_fk == MdCompany.company_pk) \
                        .filter(MdUser.user_id == user_id).first()[0]
                    if user.company_description is not None:
                        documents_list.append({
                            "document_pk": "company_description",
                                                "document_type": "learned_by_mojo",
                                                "name": f"{company_name} knowledge",
                                               "text": user.company_description,
                                               "author": user.name,
                            "creation_date": user.creation_date.isoformat(),
                            "last_update_date": user.last_company_description_update_date.isoformat() if user.last_company_description_update_date is not None else user.creation_date.isoformat()
                        })

            return {"documents": documents_list}, 200

        except Exception as e:
            log_error(f"Error getting documents : {e}")
            return {"error": f"Error getting documents : {e}"}, 500

    def delete(self, user_id):

        try:
            timestamp = request.args["datetime"]
            document_pk = request.args["document_pk"]
        except KeyError as e:
            log_error(f"Error getting messages : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        try:
            # check document for this user exists
            document: Document = db.session.query(Document) \
                .filter(Document.document_pk == document_pk) \
                .filter(Document.author_user_id == user_id) \
                .filter(Document.deleted_by_user == False) \
                .first()
            if document is None:
                return {"error": "Document not found for this user"}, 404

            # delete document
            document.deleted_by_user = True
            db.session.commit()

            return {"document_pk": document_pk}, 200

        except Exception as e:
            log_error(f"Error deleting document : {e}")
            db.session.rollback()
            return {"error": f"Error deleting document : {e}"}, 500
