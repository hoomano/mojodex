from mojodex_core.entities.db_base_entities import MdTaskPredefinedActionAssociation
from sqlalchemy.orm import object_session

from mojodex_core.entities.predefined_action_displayed_data import PredefinedActionDisplayedData

class TaskPredefinedActionAssociation(MdTaskPredefinedActionAssociation):

    @property
    def display_data(self) -> list[PredefinedActionDisplayedData]:
        try:
            session = object_session(self)

            return session.query(PredefinedActionDisplayedData) \
                .filter(PredefinedActionDisplayedData.task_predefined_action_association_fk == self.task_predefined_action_association_pk) \
                .all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: display_data :: {e}")
            

    def to_json(self):
        try:
            return {
                    "task_pk": self.predefined_action_fk,
                    "displayed_data":[display_data.to_json() for display_data in self.display_data]
                }
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: to_json :: {e}")
