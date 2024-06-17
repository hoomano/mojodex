import os

from mojodex_core.entities.db_base_entities import *
from app import db


from mojodex_backend_logger import MojodexBackendLogger

from app import model_loader
from mojodex_core.llm_engine.providers.openai_embedding import OpenAIEmbedding


class DocumentManager:
    logger_prefix = "DocumentManager"

    def __init__(self):
        self.logger = MojodexBackendLogger(f"{DocumentManager.logger_prefix}")


    def __embedded(self, text, user_id, user_task_execution_pk=None, task_name_for_system=None):
        try:
            embedding_response = model_loader.embedding_provider.embed(text, user_id,label="DOCUMENT_EMBEDDING", user_task_execution_pk=user_task_execution_pk,
                                                     task_name_for_system=task_name_for_system, )
            embedding = embedding_response["data"][0]["embedding"]
            return embedding
        except Exception as e:
            raise Exception(f"embedded : {e}")


    def get_text(self, document_pk):
        try:
            chunks = db.session.query(MdDocumentChunk.chunk_text).filter(MdDocumentChunk.document_fk == document_pk).order_by(
                MdDocumentChunk.index).all()
            chunk_text = " ".join([chunk[0] for chunk in chunks]) if chunks else ""
            return chunk_text
        except Exception as e:
            raise Exception(f"get_text : {e}")


    def retrieve(self, query, user_task_execution_pk, task_name_for_system, top_k=1):
        try:
            user_id = db.session.query(MdUser.user_id).join(MdUserTask, MdUserTask.user_id == MdUser.user_id).join(
                MdUserTaskExecution, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk).filter(
                MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk).first()[0]

            embedded_query = self.__embedded(query, user_id, user_task_execution_pk=user_task_execution_pk,
                                            task_name_for_system=task_name_for_system)


            nearest_neighbors = db.session.query(MdDocumentChunk.chunk_text, MdDocument.name) \
                .filter(MdDocumentChunk.embedding.isnot(None)) \
                .join(MdDocument, MdDocument.document_pk == MdDocumentChunk.document_fk) \
                .filter(MdDocument.author_user_id == user_id) \
                .order_by(MdDocumentChunk.embedding.cosine_distance(embedded_query)).limit(top_k).all()

            return [{
                'text': chunk_text,
                'source': document_name
            } for chunk_text, document_name in nearest_neighbors]
        except Exception as e:
            raise Exception(f"retrieve : {e}")

