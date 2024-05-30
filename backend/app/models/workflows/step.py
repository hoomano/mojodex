from abc import ABC, abstractmethod
from typing import List
from mojodex_core.db import Session
from sqlalchemy import or_, func
from mojodex_core.entities import MdWorkflowStepDisplayedData, MdWorkflowStep, MdUserTask, MdUser


class WorkflowStep(ABC):
    logger_prefix = "WorkflowStep :: "

    def __init__(self, workflow_step):
        try:
            self.db_object = workflow_step
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

    @property
    @abstractmethod
    def definition_for_system(self) -> str:
        raise NotImplementedError

    @property
    def name_for_system(self) -> str:
        return self.db_object.name_for_system

    def _get_displayed_data(self, db_session: Session, user_id: str) -> MdWorkflowStepDisplayedData:
        try:
            return db_session.query(MdWorkflowStepDisplayedData) \
                .join(MdWorkflowStep, MdWorkflowStep.workflow_step_pk == MdWorkflowStepDisplayedData.workflow_step_fk) \
                .join(MdUserTask, MdUserTask.task_fk == MdWorkflowStep.task_fk) \
                .join(MdUser, MdUser.user_id == user_id) \
                .filter(MdWorkflowStepDisplayedData.workflow_step_fk == self.db_object.workflow_step_pk) \
                .filter(or_(
                    MdWorkflowStepDisplayedData.language_code == MdUser.language_code,
                    MdWorkflowStepDisplayedData.language_code == 'en'
                )) \
                .order_by(
                # Sort by user's language first otherwise by english
                func.nullif(MdWorkflowStepDisplayedData.language_code, 'en').asc()) \
                .first()
        except Exception as e:
            raise Exception(f"_get_displayed_data :: {e}")

    def get_name_for_user(self, db_session: Session, user_id: str) -> str:
        try:
            return self._get_displayed_data(db_session, user_id).name_for_user
        except Exception as e:
            raise Exception(f"{WorkflowStep.logger_prefix} get_name_for_user :: {e}")

    def get_definition_for_user(self, db_session: Session, user_id: str) -> str:
        try:
            return self._get_displayed_data(db_session, user_id).definition_for_user
        except Exception as e:
            raise Exception(f"{WorkflowStep.logger_prefix} get_definition_for_user :: {e}")

    @property
    @abstractmethod
    def input_keys(self) -> List[str]:
        raise NotImplementedError

    @property
    @abstractmethod
    def output_keys(self) -> List[str]:
        raise NotImplementedError

    @property
    def workflow_step_pk(self) -> int:
        return self.db_object.workflow_step_pk

    @property
    def user_validation_required(self) -> bool:
        return self.db_object.user_validation_required

    @property
    def is_checkpoint(self):
        return True

    @property
    def rank(self):
        return self.db_object.rank

    @abstractmethod
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
            raise Exception(f"{WorkflowStep.logger_prefix} execute :: {e}")
