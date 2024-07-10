from mojodex_core.entities.db_base_entities import MdPredefinedActionDisplayedData, MdTaskPredefinedActionAssociation
from sqlalchemy.orm import object_session

class TaskPredefinedActionAssociation(MdTaskPredefinedActionAssociation):

    @property
    def display_data(self) -> list[MdPredefinedActionDisplayedData]:
        try:
            session = object_session(self)

            return session.query(MdPredefinedActionDisplayedData) \
                .filter(MdPredefinedActionDisplayedData.task_predefined_action_association_fk == self.task_predefined_action_association_pk) \
                .all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: display_data :: {e}")
            
