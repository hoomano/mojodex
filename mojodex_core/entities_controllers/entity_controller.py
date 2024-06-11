from abc import ABC
from mojodex_core.db import Session

class EntityController(ABC):
    def __init__(self, db_entity_class, primary_key, db_session: Session):
        self.db_entity_class = db_entity_class
        self.pk = primary_key
        self.db_session = db_session
        self.db_object = self._get_db_object(primary_key)

    def _get_db_object(self, primary_key):
        return self.db_session.query(self.db_entity_class).get(primary_key)