from app import server_socket
from mojodex_core.entities import MdUserWorkflowStepExecution, MdWorkflowStep
from typing import List
from models.workflows.steps_library import steps_class
from sqlalchemy.orm.attributes import flag_modified


class WorkflowStepExecution:
    logger_prefix = "WorkflowStepExecution"

    def __init__(self, db_session, db_object: MdUserWorkflowStepExecution, user_id):
        try:
            self.db_session = db_session
            self.db_object = db_object
            self.user_id = user_id
            self.workflow_step = steps_class[self._db_workflow_step.name_for_system](self._db_workflow_step)
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

    @property
    def _db_workflow_step(self):
        try:
            return self.db_session.query(MdWorkflowStep).filter(
                MdWorkflowStep.workflow_step_pk == self.db_object.workflow_step_fk).first()
        except Exception as e:
            raise Exception(f"_db_workflow_step :: {e}")

    @property
    def is_checkpoint(self):
        return self.workflow_step.is_checkpoint

    def execute(self, initial_parameter: dict, past_validated_steps_results: List[dict], session_id: str):
        try:
            step_json = self.to_json()
            step_json["session_id"] = session_id
            server_socket.emit('workflow_step_execution_started', step_json, to=session_id)
            self.result = self.workflow_step.execute(self.parameter, self.get_learned_instructions(), initial_parameter,
                                                     past_validated_steps_results, user_id=self.user_id)
        except Exception as e:
            raise Exception(f"execute :: {e}")

    @property
    def parameter(self):
        try:
            return self.db_object.parameter
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: parameter :: {e}")

    @property
    def result(self):
        try:
            return self.db_object.result
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: parameter :: {e}")

    @result.setter
    def result(self, value: List[dict]):
        try:
            self.db_object.result = value
            flag_modified(self.db_object, "result")
            self.db_session.commit()
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: result :: {e}")

    @property
    def validated(self):
        return self.db_object.validated

    def validate(self):
        try:
            self.db_object.validated = True
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: validate :: {e}")

    def invalidate(self, session_id: str):
        try:
            self.db_object.validated = False
            self.db_session.commit()
            # send message to user
            json_step = self.to_json()
            json_step["session_id"] = session_id
            server_socket.emit('workflow_step_execution_invalidated', json_step, to=session_id)
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: invalidate :: {e}")

    def learn_instruction(self, instruction):
        try:
            self.db_object.learned_instruction = instruction
            self.db_session.commit()
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: learn_instruction :: {e}")

    def get_learned_instructions(self):
        # find list of previous step of this kind for this workflow execution
        try:
            previous_steps_execution = self.db_session.query(MdUserWorkflowStepExecution) \
                .filter(MdUserWorkflowStepExecution.workflow_step_fk == self.db_object.workflow_step_fk) \
                .filter(
                MdUserWorkflowStepExecution.user_workflow_execution_fk == self.db_object.user_workflow_execution_fk) \
                .filter(
                MdUserWorkflowStepExecution.user_workflow_step_execution_pk != self.db_object.user_workflow_step_execution_pk) \
                .all()
            return [
                {'result': previous_step_execution.result, 'instruction': previous_step_execution.learned_instruction}
                for previous_step_execution in previous_steps_execution if
                previous_step_execution.learned_instruction and previous_step_execution.parameter == self.parameter]
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: get_learned_instructions :: {e}")

    @property
    def name_for_user(self):
        return self.workflow_step.get_name_for_user(self.db_session, self.user_id)

    @property
    def definition_for_user(self):
        return self.workflow_step.get_definition_for_user(self.db_session, self.user_id)


    @property
    def name_for_system(self):
        return self.workflow_step.name_for_system

    @property
    def definition_for_system(self):
        return self.workflow_step.definition_for_system

    def to_json(self):
        try:
            return {
                "user_workflow_step_execution_pk": self.db_object.user_workflow_step_execution_pk,
                "workflow_step_pk": self.db_object.workflow_step_fk,
                "step_name": self.name_for_user,
                "step_definition": self.definition_for_user,
                "validated": self.validated,
                "parameter": self.parameter,
                "result": self.result
            }
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: to_json :: {e}")
