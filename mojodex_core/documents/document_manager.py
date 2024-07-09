from datetime import datetime
from mojodex_core.db import with_db_session
from mojodex_core.documents.document_chunk_manager import DocumentChunkManager
from mojodex_core.embedder.embedding_service import EmbeddingService
from mojodex_core.entities.db_base_entities import MdDocument, MdDocumentChunk, MdUser, MdUserTask, MdUserTaskExecution

class DocumentManager:

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DocumentManager, cls).__new__(
                cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance


    def new_document(self, user_id, text, name, document_type, user_task_execution_pk=None, task_name_for_system=None,
                     chunk_validation_callback=None, ):
        try:
            document_pk = self._add_document_to_db(
                name, user_id, document_type)
            chunk_db_pks = DocumentChunkManager().create_document_chunks(document_pk, text,
                                                                              user_id,
                                                                              user_task_execution_pk=user_task_execution_pk,
                                                                              task_name_for_system=task_name_for_system,
                                                                              chunk_validation_callback=chunk_validation_callback)

            return document_pk
        except Exception as e:
            raise Exception(f"new_document : {e}")

    @with_db_session
    def _add_document_to_db(self, name, user_id, document_type, db_session):
        try:
            document = MdDocument(
                name=name,
                author_user_id=user_id,
                document_type=document_type,
                creation_date=datetime.now(),
            )
            db_session.add(document)
            db_session.commit()
            return document.document_pk
        except Exception as e:
            raise Exception(f"_add_document_to_db : {e}")



    @with_db_session
    def retrieve(self, query, user_task_execution_pk, task_name_for_system, db_session, top_k=1):
        try:
            user_id = db_session.query(MdUser.user_id).join(MdUserTask, MdUserTask.user_id == MdUser.user_id).join(
                MdUserTaskExecution, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk).filter(
                MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk).first()[0]

            embedded_query = EmbeddingService().embed(query, user_id, user_task_execution_pk=user_task_execution_pk,
                                            task_name_for_system=task_name_for_system)


            nearest_neighbors = db_session.query(MdDocumentChunk.chunk_text, MdDocument.name) \
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
