import os
import requests
from datetime import datetime

from models.documents.document_chunk_manager import DocumentChunkManager

from app import model_loader

from background_logger import BackgroundLogger


class DocumentManager:
    logger_prefix = "DocumentManager"

    def __init__(self):
        self.logger = BackgroundLogger(f"{DocumentManager.logger_prefix}")

        self.document_chunk_manager = DocumentChunkManager()

    def _embedded(self, text, user_id, user_task_execution_pk=None, task_name_for_system=None):
        try:
            embedding_response = model_loader.embedding_provider.embed(text, user_id, label="DOCUMENT_EMBEDDING", user_task_execution_pk=user_task_execution_pk,
                                                     task_name_for_system=task_name_for_system, )
            embedding = embedding_response["data"][0]["embedding"]
            return embedding
        except Exception as e:
            raise Exception(f"embedded : {e}")

    def new_document(self, user_id, text, name, document_type, user_task_execution_pk=None, task_name_for_system=None,
                     chunk_validation_callback=None, ):
        try:
            document_pk = self.__add_document_to_db(
                name, user_id, document_type)
            chunk_db_pks = self.document_chunk_manager.create_document_chunks(document_pk, text, self._embedded,
                                                                              user_id,
                                                                              user_task_execution_pk=user_task_execution_pk,
                                                                              task_name_for_system=task_name_for_system,
                                                                              chunk_validation_callback=chunk_validation_callback)

            return document_pk
        except Exception as e:
            raise Exception(f"new_document : {e}")

    def __add_document_to_db(self, name, user_id, document_type):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/document"
            pload = {'datetime': datetime.now().isoformat(), 'name': name, 'user_id': user_id,
                     'document_type': document_type}
            headers = {
                'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.put(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(
                    f"__add_document_to_db : {internal_request.status_code} - {internal_request.text}")
            document_pk = internal_request.json()["document_pk"]
            return document_pk
        except Exception as e:
            raise Exception(f"__add_document_to_db : {e}")

    def update_document(self, user_id, document_pk, document_chunks_pks, text, chunk_validation_callback=None):
        try:
            self.document_chunk_manager.update_document_chunks(document_pk, text, self._embedded, user_id,
                                                               chunk_validation_callback=chunk_validation_callback,
                                                               old_chunks_pks=document_chunks_pks)
            self.__save_document_to_db(document_pk)
        except Exception as e:
            self.logger.error(
                f"{DocumentManager.logger_prefix} :: update_document : {e}")
            raise Exception(
                f"{DocumentManager.logger_prefix} :: update_document : {e}")

    def __save_document_to_db(self, document_pk):
        try:
            self.logger.debug(f"__save_document_to_db : {document_pk}")
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/document"
            pload = {'datetime': datetime.now().isoformat(), 'document_pk': document_pk,
                     'update_date': datetime.now().isoformat()}
            headers = {
                'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(
                    f"__save_document_to_db : {internal_request.status_code} - {internal_request.text}")
            document_pk = internal_request.json()["document_pk"]
            return document_pk
        except Exception as e:
            raise Exception(f"__save_document_to_db : {e}")

    def retrieve(self, query, user_task_execution_pk, task_name_for_system, top_k=1):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/document_chunk"
            pload = {'datetime': datetime.now().isoformat(), 'query': query,
                     'user_task_execution_pk': user_task_execution_pk,
                     'task_name_for_system': task_name_for_system,
                     'top_k': top_k}
            headers = {
                'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.get(uri, params=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(
                    f"retrieve : {internal_request.status_code} - {internal_request.text}")

            document_chunks = internal_request.json(
            )["document_chunks"]  # [{'source': , 'text': }]
            return document_chunks

        except Exception as e:
            self.logger.error(f"retrieve : {e}")
            return None
