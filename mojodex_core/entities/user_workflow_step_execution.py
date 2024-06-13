from typing import List

from mojodex_core.entities.db_base_entities import MdUserWorkflowStepExecution, MdUserWorkflowStepExecutionResult, \
    MdWorkflowStep

import pytz
from sqlalchemy.orm import object_session

from mojodex_core.steps_library import steps_class


class UserWorkflowStepExecution(MdUserWorkflowStepExecution):

    @property
    def workflow_step(self):
        try:
            session = object_session(self)
            md_step = session.query(MdWorkflowStep).get(self.workflow_step_fk)
            step_class = steps_class[md_step.name_for_system]
            return session.query(step_class).get(self.workflow_step_fk)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: workflow_step :: {e}")

    @property
    def user_task_execution(self):
        try:
            from mojodex_core.entities.user_workflow_execution import UserWorkflowExecution
            session = object_session(self)
            return session.query(UserWorkflowExecution).get(self.user_task_execution_fk)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_task_execution :: {e}")

    @property
    def is_checkpoint(self):
        return self.workflow_step.is_checkpoint



    @property
    def creation_date_at_utc(self):
        return self.creation_date.astimezone(pytz.UTC)

    @property
    def name_for_user(self):
        return self.workflow_step.get_name_in_language(self.user_task_execution.user.language_code)

    @property
    def definition_for_user(self):
        return self.workflow_step.get_definition_in_language(self.user_task_execution.user.language_code)

    @property
    def name_for_system(self):
        return self.workflow_step.name_for_system

    @property
    def definition_for_system(self):
        return self.workflow_step.definition_for_system

    def validate(self):
        try:
            self.validated = True
            session = object_session(self)
            session.commit()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: validate :: {e}")

    def get_learned_instructions(self):
        # find list of previous step of this kind for this workflow execution
        try:
            session = object_session(self)
            previous_steps_execution = session.query(UserWorkflowStepExecution) \
                .filter(MdUserWorkflowStepExecution.workflow_step_fk == self.workflow_step_fk) \
                .filter(
                MdUserWorkflowStepExecution.user_task_execution_fk == self.user_task_execution_fk) \
                .filter(
                MdUserWorkflowStepExecution.user_workflow_step_execution_pk != self.user_workflow_step_execution_pk) \
                .all()
            return [
                {'result': previous_step_execution.result, 'instruction': previous_step_execution.learned_instruction}
                for previous_step_execution in previous_steps_execution if
                previous_step_execution.learned_instruction and previous_step_execution.parameter == self.parameter]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_learned_instructions :: {e}")

    def learn_instruction(self, instruction):
        try:
            self.learned_instruction = instruction
            session = object_session(self)
            session.commit()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: learn_instruction :: {e}")

    @property
    def result(self):
        try:
            # find the last associated step result if any
            session = object_session(self)
            step_result = session.query(MdUserWorkflowStepExecutionResult) \
                .filter(
                MdUserWorkflowStepExecutionResult.user_workflow_step_execution_fk == self.user_workflow_step_execution_pk) \
                .order_by(MdUserWorkflowStepExecutionResult.creation_date.desc()) \
                .first()
            return step_result.result if step_result else None
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: parameter :: {e}")

    @result.setter
    def result(self, value: List[dict]):
        try:
            session = object_session(self)
            step_result = MdUserWorkflowStepExecutionResult(
                user_workflow_step_execution_fk=self.user_workflow_step_execution_pk,
                result=value)
            session.add(step_result)
            session.commit()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: result :: {e}")

    def to_json(self):
        try:
            return {
                "user_workflow_step_execution_pk": self.user_workflow_step_execution_pk,
                "workflow_step_pk": self.workflow_step_fk,
                "step_name_for_user": self.name_for_user,
                "step_definition_for_user": self.definition_for_user,
                "creation_date": self.creation_date_at_utc.isoformat(),
                "user_validation_required": self.workflow_step.user_validation_required,
                "validated": self.validated,
                "parameter": self.parameter,
                "result": self.result,
                "error_status": self.error_status
            }
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: to_json :: {e}")

    def invalidate(self):
        try:
            session = object_session(self)
            self.validated = False
            session.commit()
            # TODO: move that to the call of this function

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: invalidate :: {e}")



