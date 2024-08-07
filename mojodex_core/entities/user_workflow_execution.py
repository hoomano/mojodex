from functools import cached_property
from mojodex_core.entities.db_base_entities import MdWorkflowStep
from mojodex_core.entities.user_task_execution import UserTaskExecution
from mojodex_core.entities.user_workflow import UserWorkflow
from mojodex_core.entities.user_workflow_step_execution import UserWorkflowStepExecution
from sqlalchemy.orm import object_session
from sqlalchemy import case


class UserWorkflowExecution(UserTaskExecution):

    @cached_property
    def user_task(self) -> UserWorkflow:
        try:
            session = object_session(self)
            return session.query(UserWorkflow).get(self.user_task_fk)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: user_task :: {e}")

    @cached_property
    def last_step_execution(self):
        try:
            session = object_session(self)
            return session.query(UserWorkflowStepExecution) \
                .filter(UserWorkflowStepExecution.user_task_execution_fk == self.user_task_execution_pk) \
                .order_by(UserWorkflowStepExecution.creation_date.desc()) \
                .first()
        except Exception as e:
            raise Exception(f"last_step_execution :: {e}")

    @cached_property
    def past_valid_step_executions(self):
        try:
            session = object_session(self)
            return session.query(UserWorkflowStepExecution) \
                .join(MdWorkflowStep, UserWorkflowStepExecution.workflow_step_fk == MdWorkflowStep.workflow_step_pk) \
                .filter(
                case(
                    # When `MdWorkflowStep.user_validation_required` is `True`, we check that `MdUserWorkflowStepExecution.validated` is also `True`

                    (MdWorkflowStep.user_validation_required == True, UserWorkflowStepExecution.validated == True),

                    # if `user_validation_required` is `False`, we don't care about the `validated` status, and the `MdUserWorkflowStepExecution` will be included in the results regardless of its `validated` value.
                    else_=True
                )
            ) \
                .filter(UserWorkflowStepExecution.user_task_execution_fk == self.user_task_execution_pk) \
                .filter(UserWorkflowStepExecution.error_status.is_(None)) \
                .order_by(UserWorkflowStepExecution.creation_date.asc()) \
                .all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: past_valid_step_executions :: {e}")

    @cached_property
    def steps_execution_as_json(self):
        try:
            validated_steps_json = [step_execution.to_json() for step_execution in self.past_valid_step_executions]
            last_step_execution = self.last_step_execution
            if last_step_execution and last_step_execution.validated is None and (
                    last_step_execution.workflow_step.user_validation_required or last_step_execution.error_status):
                validated_steps_json.append(last_step_execution.to_json())
            return validated_steps_json
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: get_steps_execution_json :: {e}")

    def count_valid_step_executions_of_a_step(self, workflow_step_pk):
        """
        Count the number of valid step executions of a given step for the current workflow execution.
        :param workflow_step_pk:
        :return:
        """
        try:
            session = object_session(self)
            return session.query(UserWorkflowStepExecution) \
                .join(MdWorkflowStep,
                      UserWorkflowStepExecution.workflow_step_fk == MdWorkflowStep.workflow_step_pk) \
                .filter(
                UserWorkflowStepExecution.user_task_execution_fk == self.user_task_execution_pk) \
                .filter(
                UserWorkflowStepExecution.workflow_step_fk == workflow_step_pk) \
                .filter(
                case(
                    # When `MdWorkflowStep.user_validation_required` is `True`, we check that `MdUserWorkflowStepExecution.validated` is also `True`
                    (MdWorkflowStep.user_validation_required == True,
                     UserWorkflowStepExecution.validated == True),
                    # if `user_validation_required` is `False`, we don't care about the `validated` status, and the `MdUserWorkflowStepExecution` will be included in the results regardless of its `validated` value.
                    else_=True
                )) \
                .filter(UserWorkflowStepExecution.error_status.is_(None)) \
                .count()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: count_valid_step_executions_of_a_step :: {e}")

    def get_last_execution_of_a_step(self, workflow_step_pk):
        """
        Get the last execution of a given step for the current workflow execution.
        :param workflow_step_pk:
        :return:
        """
        try:
            session = object_session(self)
            return session.query(UserWorkflowStepExecution) \
                .filter(
                UserWorkflowStepExecution.user_task_execution_fk == self.user_task_execution_pk) \
                .filter(UserWorkflowStepExecution.workflow_step_fk == workflow_step_pk) \
                .order_by(UserWorkflowStepExecution.creation_date.desc()) \
                .first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_last_execution_of_a_step :: {e}")

    def get_valid_executions_of_a_step(self,workflow_step_pk):
        """
        Get the valid executions of a given step for the current workflow execution.
        Ordered by creation date in ascending order. (The oldest first)
        :param workflow_step_pk:
        :return:
        """
        try:
            session = object_session(self)
            return session.query(UserWorkflowStepExecution) \
                .join(MdWorkflowStep,
                      UserWorkflowStepExecution.workflow_step_fk == MdWorkflowStep.workflow_step_pk) \
                .filter(
                UserWorkflowStepExecution.user_task_execution_fk == self.user_task_execution_pk) \
                .filter(
                UserWorkflowStepExecution.workflow_step_fk == workflow_step_pk) \
                .filter(
                case(
                    # When `MdWorkflowStep.user_validation_required` is `True`, we check that `MdUserWorkflowStepExecution.validated` is also `True`
                    (MdWorkflowStep.user_validation_required == True,
                     UserWorkflowStepExecution.validated == True),
                    # if `user_validation_required` is `False`, we don't care about the `validated` status, and the `MdUserWorkflowStepExecution` will be included in the results regardless of its `validated` value.
                    else_=True
                )) \
                .filter(UserWorkflowStepExecution.error_status.is_(None)) \
                .order_by(UserWorkflowStepExecution.creation_date.asc()) \
                .all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_valid_executions_of_a_step :: {e}")

    @cached_property
    def result(self):
        """
        For now, result of a workflow is the concatenation of results of all last step's validated executions' results
        """
        try:
            last_step = self.task.steps[-1]
            validated_last_step_executions = self.get_valid_executions_of_a_step(last_step.workflow_step_pk)
            return "\n\n".join([list(step.result[0].values())[0] for step in validated_last_step_executions])
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: result :: {e}")
        

    def to_json(self):
        try:
            # return super().to_json() and add keys steps and step_executions 
            return {
                    **super().to_json(),
                    "steps": self.user_task.steps_as_json,
                    "step_executions": self.steps_execution_as_json,
                    }
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: to_json :: {e}")
