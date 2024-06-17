from abc import ABC, abstractmethod
from typing import List

from mojodex_core.entities.abstract_entities.abstract_entity import AbstractEntity
from mojodex_core.entities.db_base_entities import MdWorkflowStep, MdWorkflowStepDisplayedData
from sqlalchemy.orm import object_session
from sqlalchemy import func, or_

class WorkflowStep(MdWorkflowStep, ABC, metaclass=AbstractEntity):
    """WorkflowStep entity class is an abstract class.
    It should be instanciated as a class listed in `mojodex_core/steps_library.py`.
    
    This is true for default constructor usage but also when retrieving data from the database: `db.session.query(...)...`"""

    types_reserved_key = 'types'
    reserved_output_keys: List[str] = [types_reserved_key]

    @property
    @abstractmethod
    def definition_for_system(self) -> str:
        raise NotImplementedError

    @property
    def name_for_system(self) -> str:
        return self.name_for_system

    def _get_displayed_data(self, language_code):
        try:
            session = object_session(self)
            return session.query(MdWorkflowStepDisplayedData) \
                .filter(MdWorkflowStepDisplayedData.workflow_step_fk == self.workflow_step_pk) \
                .filter(or_(
                MdWorkflowStepDisplayedData.language_code == language_code,
                MdWorkflowStepDisplayedData.language_code == 'en'
            )) \
                .order_by(
                # Sort by user's language first otherwise by english
                func.nullif(MdWorkflowStepDisplayedData.language_code, 'en').asc()) \
                .first()
        except Exception as e:
            raise Exception(f"_get_displayed_data_in_language :: {e}")

    def get_name_in_language(self, language_code):
        try:
            return self._get_displayed_data(language_code).name_for_user
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_name_in_language :: {e}")

    def get_definition_in_language(self, language_code):
        try:
            return self._get_displayed_data(language_code).definition_for_user
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_definition_in_language :: {e}")

    @property
    @abstractmethod
    def input_keys(self) -> List[str]:
        raise NotImplementedError

    @property
    @abstractmethod
    def output_keys(self) -> List[str]:
        raise NotImplementedError

    @property
    def is_checkpoint(self):
        return True

    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameters: dict,
                 past_validated_steps_results: List[dict], user_id: str, user_task_execution_pk: int,
                 task_name_for_system: str, session_id: str):
        pass

    def execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict,
                past_validated_steps_results: List[dict], user_id: str, user_task_execution_pk: int,
                task_name_for_system: str, session_id: str):
        """
        Returns a list of parameters (dict)
        """
        try:

            # ensure that input keys are present in parameter
            for key in self.input_keys:
                if key not in parameter:
                    raise Exception(f"execute :: key {key} not in parameter")
            output = self._execute(parameter, learned_instructions, initial_parameter, past_validated_steps_results,
                                   user_id, user_task_execution_pk, task_name_for_system, session_id)  # list of dict
            # ensure output is a list
            if not isinstance(output, List):
                raise Exception(f"execute :: output is not a list")
            # ensure that output keys are present in output
            for item in output:
                if not isinstance(item, dict):
                    raise Exception(f"execute :: output item {item} is not a dict")
                for key in self.output_keys:
                    if key not in item:
                        raise Exception(f"execute :: key {key} not in output")
            return output
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} execute :: {e}")
