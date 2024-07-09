from mojodex_core.entities.db_base_entities import MdDocumentChunk
from sqlalchemy.orm import object_session
from datetime import datetime

class DocumentChunk(MdDocumentChunk):

    def update(self, chunk_text, embedding):
        try:
            session = object_session(self)
            self.chunk_text = chunk_text
            self.embedding = embedding
            session.commit()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}: update : {e}")
        
    def delete(self):
        try:
            session = object_session(self)
            self.deleted = datetime.now()
            session.commit()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}: delete : {e}")
