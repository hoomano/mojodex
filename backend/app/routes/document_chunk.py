import os
from datetime import datetime

from flask import request
from flask_restful import Resource
from app import db, document_manager
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *


class DocumentChunk(Resource):

    def put(self):
        log_message = "Error creating document_chunk"
        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"{log_message} : Authentication error")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"{log_message} : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        if not request.is_json:
            return {"error": "Request must be in json format"}, 400

        try:
            timestamp = request.json["datetime"]
            document_fk = request.json["document_fk"]
            chunk_index = request.json["chunk_index"]
            chunk_text = request.json["chunk_text"]
            embedding = request.json["embedding"]
        except KeyError as e:
            return {"error": f"Missing key {e} in json"}, 400

        try:
            chunk_db = MdDocumentChunk(document_fk=document_fk, index=chunk_index, chunk_text=chunk_text, embedding=embedding)
            db.session.add(chunk_db)
            db.session.commit()
            db.session.refresh(chunk_db)

            return {"document_chunk_pk": chunk_db.document_chunk_pk}, 200
        except Exception as e:
            log_error(f"{log_message}: {e}")
            return {"error": f"{log_message}: {e}"}, 500


    def post(self):
        log_message = "Error updating document_chunk"
        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"{log_message} : Authentication error")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"{log_message} : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        if not request.is_json:
            return {"error": "Request must be in json format"}, 400

        try:
            timestamp = request.json["datetime"]
            chunk_pk = request.json["chunk_pk"]
            chunk_text = request.json["chunk_text"]
            embedding = request.json["embedding"]
        except KeyError as e:
            return {"error": f"Missing key {e} in json"}, 400

        try:
            chunk = db.session.query(MdDocumentChunk).filter(MdDocumentChunk.document_chunk_pk == chunk_pk).first()
            if chunk is None:
                return {"error": f"Chunk not found"}, 404
            chunk.chunk_text = chunk_text
            chunk.embedding = embedding
            db.session.commit()

            return {"document_chunk_pk": chunk.document_chunk_pk}, 200
        except Exception as e:
            log_error(f"{log_message} : {e}")
            return {"error": f"{log_message}: {e}"}, 500


    def delete(self):
        log_message = "Error deleting document_chunk"
        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"{log_message}: Authentication error")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"{log_message}: Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.args["datetime"]
            chunk_pk = request.args["chunk_pk"]
        except KeyError as e:
            return {"error": f"Missing key {e} in json"}, 400

        try:
            chunk = db.session.query(MdDocumentChunk).filter(MdDocumentChunk.document_chunk_pk == chunk_pk).first()
            if chunk is None:
                return {"error": f"Chunk not found"}, 404

            chunk.deleted = datetime.now()
            db.session.commit()
            return {"document_chunk_pk": chunk.document_chunk_pk}, 200
        except Exception as e:
            log_error(f"{log_message} : {e}")
            return {"error": f"{log_message}: {e}"}, 500


    def get(self):
        log_message = "Error retrieving document_chunk"
        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"{log_message} : Authentication error")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"{log_message} : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.args["datetime"]
            query = request.args["query"]
            user_task_execution_pk = request.args["user_task_execution_pk"]
            task_name_for_system = request.args["task_name_for_system"]
            top_k = request.args["top_k"]
        except KeyError as e:
            return {"error": f"Missing key {e} in args"}, 400

        try:
            document_chunks = document_manager.retrieve(query, user_task_execution_pk, task_name_for_system, top_k=top_k)

            return {"document_chunks": document_chunks}, 200

        except Exception as e:
            log_error(f"{log_message}: {e}")
            return {"error": f"{log_message}: {e}"}, 500