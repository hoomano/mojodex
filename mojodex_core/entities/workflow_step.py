from functools import cached_property
from typing import List
from mojodex_core.entities.db_base_entities import MdWorkflowStep, MdWorkflowStepDisplayedData
from sqlalchemy.orm import object_session
from sqlalchemy import func, or_

from mojodex_core.entities.workflow_step_displayed_data import WorkflowStepDisplayedData

class WorkflowStep(MdWorkflowStep):
    """WorkflowStep contains additional properties and methods for a WorkflowStep entity."""

    types_reserved_key = 'types'
    reserved_output_keys: List[str] = [types_reserved_key]


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
            raise Exception(f"_get_displayed_data :: {e}")

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


    def _get_relative_step_by_rank(self, relative_rank: int):
        """
        Get the relative step of a workflow step by its rank."""
        try:
            session = object_session(self)
            return session.query(MdWorkflowStep) \
                .filter(MdWorkflowStep.task_fk == self.task_fk) \
                .filter(MdWorkflowStep.rank == self.rank + relative_rank) \
                .first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: _get_relative_step_by_rank :: {e}")

    @cached_property
    def dependency_step(self):
        """The dependency step of a workflow step is the step of its workflow which rank is the previous one."""
        try:
            return self._get_relative_step_by_rank(-1)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: dependency_step :: {e}")

    @cached_property
    def next_step(self):
        """
        The next step of a workflow step is the step of its workflow which rank is the next one.
        """
        try:
            return self._get_relative_step_by_rank(+1)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: next_step :: {e}")

    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameters: dict,
                 past_validated_steps_results: List[dict], user_id: str, user_task_execution_pk: int,
                 task_name_for_system: str, session_id: str):
        """ The child of the workflow step must implement this method.
            If not, it will raise a NotImplementedError.
            This can happen for "deprecated" steps that are not used anymore.
        """
        raise NotImplementedError

    def execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict,
                past_validated_steps_results: List[dict], user_id: str, user_task_execution_pk: int,
                task_name_for_system: str, session_id: str):
        """
        Execute the workflow step.
        See [Workflow Doc](/docs/design-principles/workflows/execute_workflow.md) for more details.
        """
        try:

            output = self._execute(parameter, learned_instructions, initial_parameter, past_validated_steps_results,
                                   user_id, user_task_execution_pk, task_name_for_system, session_id)  # list of dict
            # ensure output is a list
            if not isinstance(output, List):
                raise Exception(f"execute :: output is not a list")
            # ensure that output keys are present in output
            for item in output:
                if not isinstance(item, dict):
                    raise Exception(f"execute :: output item {item} is not a dict")

            return output
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} execute :: {e}")

    
    @cached_property
    def display_data(self) -> list[WorkflowStepDisplayedData]:
        try:
            session = object_session(self)
            return session.query(WorkflowStepDisplayedData) \
                .filter(WorkflowStepDisplayedData.workflow_step_fk == self.workflow_step_pk) \
                .all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: display_data :: {e}")
    
    def to_json(self):
        try:
            return {
                "step_pk": self.workflow_step_pk,
                    "name_for_system": self.name_for_system,
                    "definition_for_system": self.definition_for_system,
                    "rank": self.rank,
                    "step_displayed_data": [display_data.to_json() for display_data in self.display_data],
                    "review_chat_enabled": self.review_chat_enabled
            }
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : to_json :: {e}")