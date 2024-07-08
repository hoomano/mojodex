
from mojodex_core.documents.document_chunk_manager import DocumentChunkManager
from mojodex_core.documents.document_manager import DocumentManager
from mojodex_core.entities.db_base_entities import MdDocument, MdDocumentChunk
from sqlalchemy.orm import object_session
from datetime import datetime, timezone

class Document(MdDocument):

    @property
    def text(self):
        try:
            session = object_session(self)
            chunks = session.query(MdDocumentChunk.chunk_text).\
                filter(MdDocumentChunk.document_fk == self.document_pk).\
                order_by(MdDocumentChunk.index).all()
            chunk_text = " ".join([chunk[0] for chunk in chunks]) if chunks else ""
            return chunk_text
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: text :: {e}")
        
    def update(self, new_text, chunk_validation_callback=None):
        try:
            DocumentChunkManager().update_document_chunks(self.document_pk, new_text, DocumentManager().embed, self.author_user_id,
                                                                chunk_validation_callback=chunk_validation_callback,
                                                                old_chunks_pks=[chunk.document_chunk_pk for chunk in self.chunks])
            self.last_update_date = datetime.now(timezone.utc)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: update_document : {e}")
        
    @property
    def chunks(self):
        try:
            session = object_session(self)
            return session.query(MdDocumentChunk).\
                filter(MdDocumentChunk.document_fk == self.document_pk).\
                order_by(MdDocumentChunk.index).all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: chunks :: {e}")