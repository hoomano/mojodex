from datetime import datetime

from app import server_socket, socketio_message_sender

from models.produced_text_managers.workflow_produced_text_manager import WorkflowProducedTextManager
from mojodex_core.entities.db_base_entities import MdUserTask, MdUserWorkflowStepExecutionResult, MdWorkflowStep
from mojodex_core.db import engine, Session
from typing import List

from mojodex_core.entities.user_task_execution import generate_title_and_summary
from mojodex_core.entities.user_workflow_execution import UserWorkflowExecution
from sqlalchemy import case, and_

from mojodex_core.entities.user_workflow_step_execution import UserWorkflowStepExecution
from mojodex_core.mail import send_technical_error_email


class WorkflowProcessController:
    logger_prefix = "WorkflowProcessController :: "

    def __del__(self):
        self.db_session.close()

    def __init__(self, workflow_execution_pk):
        try:
            self.db_session = Session(engine)
            self.workflow_execution = self.db_session.query(UserWorkflowExecution).get(workflow_execution_pk)
            self._current_step = None
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

    def _generate_new_step_execution(self, step, parameter: dict):
        try:
            workflow_step_execution = UserWorkflowStepExecution(
                user_task_execution_fk=self.workflow_execution.user_task_execution_pk,
                workflow_step_fk=step.workflow_step_pk,
                parameter=parameter
            )
            self.db_session.add(workflow_step_execution)
            self.db_session.commit()
            return workflow_step_execution
        except Exception as e:
            raise Exception(f"_generate_new_step_execution :: {e}")

    def _get_next_step_execution_to_run(self):
        try:
            if not self.workflow_execution.past_valid_step_executions:  # no step validated yet
                self._current_step = self._generate_new_step_execution(self.workflow_execution.task.steps[0],
                                                                       self.get_formatted_initial_parameters())  # of first step
                return self._current_step
            last_validated_step_execution = self.workflow_execution.past_valid_step_executions[-1]
            if len(self.workflow_execution.past_valid_step_executions) > 1:  # no dependency as it was the first step
                db_dependency_step = self.db_session.query(MdWorkflowStep) \
                    .join(MdUserTask, MdUserTask.task_fk == MdWorkflowStep.task_fk) \
                    .filter(MdUserTask.user_task_pk == self.workflow_execution.user_task_fk) \
                    .filter(MdWorkflowStep.rank == last_validated_step_execution.workflow_step.rank - 1) \
                    .first()

                # find last execution of dependency step
                db_dependency_step_execution = self.db_session.query(UserWorkflowStepExecution) \
                    .filter(
                    UserWorkflowStepExecution.user_task_execution_fk == self.workflow_execution.user_task_execution_pk) \
                    .filter(UserWorkflowStepExecution.workflow_step_fk == db_dependency_step.workflow_step_pk) \
                    .order_by(UserWorkflowStepExecution.creation_date.desc()) \
                    .first()
                db_dependency_step_execution_result = self.db_session.query(MdUserWorkflowStepExecutionResult) \
                    .filter(
                    MdUserWorkflowStepExecutionResult.user_workflow_step_execution_fk == db_dependency_step_execution.user_workflow_step_execution_pk) \
                    .order_by(MdUserWorkflowStepExecutionResult.creation_date.desc()) \
                    .first()

                # load all validated step executions of current step:
                current_step_executions_count = self.db_session.query(UserWorkflowStepExecution) \
                    .join(MdWorkflowStep,
                          UserWorkflowStepExecution.workflow_step_fk == MdWorkflowStep.workflow_step_pk) \
                    .filter(
                    UserWorkflowStepExecution.user_task_execution_fk == self.workflow_execution.user_task_execution_pk) \
                    .filter(
                    UserWorkflowStepExecution.workflow_step_fk == last_validated_step_execution.workflow_step.workflow_step_pk) \
                    .filter(
                    case(
                        # When `MdWorkflowStep.user_validation_required` is `True`, we check that `MdUserWorkflowStepExecution.validated` is also `True`
                        [
                            (MdWorkflowStep.user_validation_required == True,
                             UserWorkflowStepExecution.validated == True),
                        ],
                        # if `user_validation_required` is `False`, we don't care about the `validated` status, and the `MdUserWorkflowStepExecution` will be included in the results regardless of its `validated` value.
                        else_=True
                    )) \
                    .filter(UserWorkflowStepExecution.error_status.is_(None)) \
                    .count()

                # have all parameters been executed and validated?
                if current_step_executions_count < len(db_dependency_step_execution_result.result):
                    current_parameter = db_dependency_step_execution_result.result[current_step_executions_count]
                    self._current_step = self._generate_new_step_execution(last_validated_step_execution.workflow_step,
                                                                           current_parameter)
                    return self._current_step

            # else, generate new step execution of next step
            next_step = self.db_session.query(MdWorkflowStep) \
                .join(MdUserTask, MdUserTask.task_fk == MdWorkflowStep.task_fk) \
                .filter(MdUserTask.user_task_pk == self.workflow_execution.user_task_fk) \
                .filter(MdWorkflowStep.rank == last_validated_step_execution.workflow_step.rank + 1) \
                .first()
            # Reached last rank order => there is no next step
            if next_step is None:
                return None  # end of workflow
            # else
            self._current_step = self._generate_new_step_execution(next_step, last_validated_step_execution.result[0])
            return self._current_step
        except Exception as e:
            raise Exception(f"_get_next_step_execution_to_run :: {e}")

    def get_formatted_initial_parameters(self):
        # self.json_inputs is [{"input_name": "<input_name>", "default_value": "<value>"}]'
        # initial_parameters is {"<input_name>": "<value>", ...}
        try:
            return {input["input_name"]: input["value"] for input in self.workflow_execution.json_input_values}
        except Exception as e:
            raise Exception(f"get_formatted_initial_parameters :: {e}")

    def run(self):
        try:
            if not self.workflow_execution.title:
                server_socket.start_background_task(generate_title_and_summary, self.workflow_execution.user_task_execution_pk)
            next_step_execution_to_run = self._get_next_step_execution_to_run()
            if not next_step_execution_to_run:
                self.end_workflow_execution()
                return

            self.execute_step(next_step_execution_to_run)

            self._send_ended_step_event()
            if not next_step_execution_to_run.workflow_step.user_validation_required and next_step_execution_to_run.error_status is None:
                # add previous step to past_accepted_steps_executions
                self.workflow_execution.past_valid_step_executions.append(next_step_execution_to_run)
                self.run()
        except Exception as e:
            print(f"🔴 {self.logger_prefix} - run :: {e}")
            socketio_message_sender.send_error(f"Error during workflow run: {e}", self.workflow_execution.session_id,
                                               user_task_execution_pk=self.workflow_execution.user_task_execution_pk)

    def end_workflow_execution(self):
        try:
            produced_text, produced_text_version = self._generate_produced_text()
            server_socket.emit('workflow_execution_produced_text', {
                "user_task_execution_pk": self.workflow_execution.user_task_execution_pk,
                "produced_text": produced_text_version.production,
                "produced_text_title": produced_text_version.title,
                "produced_text_pk": produced_text.produced_text_pk,
                "produced_text_version_pk": produced_text_version.produced_text_version_pk,
                "session_id": self.workflow_execution.session_id
            }, to=self.workflow_execution.session_id)
        except Exception as e:
            raise Exception(f"end_workflow_execution :: {e}")

    def _generate_produced_text(self):
        try:
            # concatenation of results of last step's validated executions
            last_step = self.workflow_execution.task.steps[-1]
            validated_last_step_executions = self.db_session.query(UserWorkflowStepExecution) \
                .filter(
                UserWorkflowStepExecution.user_task_execution_fk == self.workflow_execution.user_task_execution_pk) \
                .filter(
                UserWorkflowStepExecution.workflow_step_fk == last_step.workflow_step_pk) \
                .filter(
                case(
                    # When `MdWorkflowStep.user_validation_required` is `True`, we check that `MdUserWorkflowStepExecution.validated` is also `True`
                    [
                        (
                            MdWorkflowStep.user_validation_required == True,
                            UserWorkflowStepExecution.validated == True),
                    ],
                    # if `user_validation_required` is `False`, we don't care about the `validated` status, and the `MdUserWorkflowStepExecution` will be included in the results regardless of its `validated` value.
                    else_=True
                )
            ) \
                .filter(UserWorkflowStepExecution.error_status.is_(None)) \
                .order_by(UserWorkflowStepExecution.creation_date.desc()) \
                .all()

            production = "\n\n".join(
                [list(step.result[0].values())[0] for step in validated_last_step_executions[::-1]])

            produced_text_manager = WorkflowProducedTextManager(self.workflow_execution.session_id,
                                                                self.workflow_execution.user.user_id,
                                                                self.workflow_execution.user_task_execution_pk)
            produced_text, produced_text_version = produced_text_manager.save(production,
                                                                              text_type_pk=self.workflow_execution.task.output_text_type_fk, )
            return produced_text, produced_text_version

        except Exception as e:
            raise Exception(f"_generate_produced_text :: {e}")

    def _send_ended_step_event(self):
        try:
            step_execution_json = self._current_step.to_json()
            step_execution_json["session_id"] = self.workflow_execution.session_id
            server_socket.emit('workflow_step_execution_ended', step_execution_json,
                               to=self.workflow_execution.session_id)
        except Exception as e:
            raise Exception(f"_send_ended_step_event :: {e}")

    def validate_step_execution(self, step_execution_pk: int):
        try:
            step_execution = self.db_session.query(UserWorkflowStepExecution).get(step_execution_pk)
            step_execution.validate()
            self.workflow_execution.past_valid_step_executions.append(step_execution)
        except Exception as e:
            raise Exception(f"validate_step_execution :: {e}")

    def invalidate_current_step(self, learned_instruction):
        try:
            current_step_in_validation = self.workflow_execution.last_step_execution
            self._invalidate_step(current_step_in_validation)
            if current_step_in_validation.workflow_step.is_checkpoint:
                current_step_in_validation.learn_instruction(learned_instruction)
                return

            # find checkpoint step
            checkpoint_step = self.workflow_execution.checkpoint_step
            # for all step in self.validated_steps_executions after checkpoint_step, invalidate them
            checkpoint_step_index = self.workflow_execution.past_valid_step_executions.index(checkpoint_step)
            for validated_step in self.workflow_execution.past_valid_step_executions[checkpoint_step_index:]:
                self._invalidate_step(validated_step)
                # remove from validated_steps_executions
                self.workflow_execution.past_valid_step_executions.remove(validated_step)
            checkpoint_step.learn_instruction(learned_instruction)
        except Exception as e:
            raise Exception(f"invalidate_current_step :: {e}")

    def _invalidate_step(self, step):
        try:
            step.invalidate()
            # send message to user
            json_step = step.to_json()
            json_step["session_id"] = self.workflow_execution.session_id
            server_socket.emit('workflow_step_execution_invalidated', json_step, to=self.workflow_execution.session_id)
        except Exception as e:
            raise Exception(f"_invalidate_step :: {e}")

    def restart(self):
        try:
            current_step_in_validation = self.workflow_execution.last_step_execution
            if current_step_in_validation.workflow_step.rank != 1:
                raise Exception("Can only restart from first step")
            self._invalidate_step(current_step_in_validation)
            # restart
            self.run()
        except Exception as e:
            raise Exception(f"restart :: {e}")

    def get_before_checkpoint_validated_steps_executions(self, current_step_in_validation: UserWorkflowStepExecution) -> \
            List[UserWorkflowStepExecution]:
        try:
            if current_step_in_validation.workflow_step.is_checkpoint:
                return self.workflow_execution.past_valid_step_executions
            checkpoint_step = self.workflow_execution.checkpoint_step
            if not checkpoint_step:
                return []
            checkpoint_step_index = self.workflow_execution.past_valid_step_executions.index(checkpoint_step)
            return self.workflow_execution.past_valid_step_executions[:checkpoint_step_index]
        except Exception as e:
            raise Exception(f"before_checkpoint_steps_executions :: {e}")

    def get_after_checkpoint_validated_steps_executions(self, current_step_in_validation: UserWorkflowStepExecution) -> \
            List[UserWorkflowStepExecution]:
        try:
            if current_step_in_validation.workflow_step.is_checkpoint:
                return []
            checkpoint_step = self.workflow_execution.checkpoint_step
            if not checkpoint_step:
                return self.workflow_execution.past_valid_step_executions
            checkpoint_step_index = self.workflow_execution.past_valid_step_executions.index(checkpoint_step)
            return self.workflow_execution.past_valid_step_executions[checkpoint_step_index:]
        except Exception as e:
            raise Exception(f"after_checkpoint_to_current_steps_executions :: {e}")

    def get_formatted_past_validated_steps_results(self):
        try:
            return [{
                "result": step.result,
                "instruction": step.learned_instruction,
                "parameter": step.parameter
            } for step in self.workflow_execution.past_valid_step_executions]
        except Exception as e:
            raise Exception(f"get_formatted_past_validated_steps_results :: {e}")

    def execute_step(self, workflow_step_execution: UserWorkflowStepExecution):
        try:

            step_json = workflow_step_execution.to_json()
            step_json["session_id"] = self.workflow_execution.session_id
            server_socket.emit('workflow_step_execution_started', step_json, to=self.workflow_execution.session_id)
            workflow_step_execution.result = workflow_step_execution.workflow_step.execute(
                workflow_step_execution.parameter,
                workflow_step_execution.get_learned_instructions(), self.get_formatted_initial_parameters(),
                self.get_formatted_past_validated_steps_results(),
                user_id=workflow_step_execution.user_task_execution.user.user_id,
                user_task_execution_pk=self.workflow_execution.user_task_execution_pk,
                task_name_for_system=self.workflow_execution.task.name_for_system,
                session_id=self.workflow_execution.session_id)
        except Exception as e:
            workflow_step_execution.error_status = {"datetime": datetime.now().isoformat(), "error": str(e)}
            self.db_session.commit()
            # send email to admin
            print(f"🔴 {self.logger_prefix} - execute_step :: {e}")
            send_technical_error_email(
                f"Error while executing step {workflow_step_execution.user_workflow_step_execution_pk} for user {workflow_step_execution.user_task_execution.user.user_id} : {e}")
