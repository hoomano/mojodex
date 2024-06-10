# entity_factory.py
from sqlalchemy.orm import Session
from registry import ModelRegistry
from sqlalchemy.exc import IntegrityError

class EntityFactory:
    def __init__(self, session: Session):
        self.session = session

    def get_entity(self, entity_type: str, entity_id: int):
        EntityModel = ModelRegistry.get(entity_type)
        if EntityModel is None:
            raise ValueError(f"Entity type {entity_type} is not registered.")

        entity = self.session.get(EntityModel, entity_id)
        if entity is None:
            raise ValueError(f"{entity_type} with id {entity_id} does not exist.")
        return entity

    def add_entity(self, entity_type: str, **kwargs):
        try:
            EntityModel = ModelRegistry.get(entity_type)
            if EntityModel is None:
                raise ValueError(f"Entity type {entity_type} is not registered.")

            entity = EntityModel(**kwargs)
            self.session.add(entity)
            self.session.commit()
            return entity
        except IntegrityError as e:
            raise Exception(f"Error adding {entity_type} entity: {e}")



