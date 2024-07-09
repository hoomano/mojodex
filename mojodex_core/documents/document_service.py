from mojodex_core.db import with_db_session
from mojodex_core.embedder.embedding_service import EmbeddingService
from mojodex_core.entities.document import Document
from mojodex_core.entities.document_chunk import DocumentChunk
from mojodex_core.entities.user_task_execution import UserTaskExecution
from datetime import datetime


class DocumentService:

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DocumentService, cls).__new__(
                cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance


    @with_db_session
    def new_document(self, user_id, text, name, document_type, db_session, user_task_execution_pk=None, task_name_for_system=None,
                     chunk_validation_callback=None):
        try:
            document = Document(
                name=name,
                author_user_id=user_id,
                document_type=document_type,
                creation_date=datetime.now(),
            )
            db_session.add(document)
            db_session.commit()
            document.create_document_chunks(text, user_id,
                                            user_task_execution_pk=user_task_execution_pk,
                                            task_name_for_system=task_name_for_system,
                                            chunk_validation_callback=chunk_validation_callback)

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : new_document : {e}")


    @with_db_session
    def retrieve(self, query, user_task_execution_pk, task_name_for_system, db_session, top_k=1):
        try:
            user_task_execution: UserTaskExecution = db_session.query(UserTaskExecution).get(user_task_execution_pk)
            user_id = user_task_execution.user.user_id

            embedded_query = EmbeddingService().embed(query, user_id, user_task_execution_pk=user_task_execution_pk,
                                            task_name_for_system=task_name_for_system)


            nearest_neighbors = db_session.query(DocumentChunk.chunk_text, Document.name) \
                .join(Document, Document.document_pk == DocumentChunk.document_fk) \
                .filter(DocumentChunk.embedding.isnot(None)) \
                .filter(Document.author_user_id == user_id) \
                .filter(Document.deleted_by_user.isnot(None)) \
                .order_by(DocumentChunk.embedding.cosine_distance(embedded_query)) \
                .limit(top_k) \
                .all()

            return [{
                'text': chunk_text,
                'source': document_name
            } for chunk_text, document_name in nearest_neighbors]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : retrieve : {e}")
