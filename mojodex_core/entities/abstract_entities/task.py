from abc import ABC

from mojodex_core.entities.abstract_entities.abstract_entity import AbstractEntity
from mojodex_core.entities.db_base_entities import MdTask, MdTaskDisplayedData
from sqlalchemy.orm import object_session
from sqlalchemy import func, or_

class Task(MdTask, ABC, metaclass=AbstractEntity):
    """Task entity class is an abstract class.
    It should be instanciated as an InstructTask or Workflow.
    
    This is true for default constructor usage but also when retrieving data from the database: `db.session.query(InstructTask).all()`"""

    def _get_displayed_data_in_language(self, language_code):
        try:
            session = object_session(self)
            return session.query(MdTaskDisplayedData).filter(MdTaskDisplayedData.task_fk == self.task_pk) \
                .filter(
                or_(
                    MdTaskDisplayedData.language_code == language_code,
                    MdTaskDisplayedData.language_code == 'en'
                )
            ).order_by(
                # Sort by user's language first otherwise by english
                func.nullif(MdTaskDisplayedData.language_code, 'en').asc()
            ).first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: _get_displayed_data_in_language :: {e}")

    def get_name_in_language(self, language_code):
        try:
            return self._get_displayed_data_in_language(language_code).name_for_user
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_name_in_language :: {e}")

    def get_json_input_in_language(self, language_code):
        try:
            return self._get_displayed_data_in_language(language_code).json_input
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_json_input_in_language :: {e}")