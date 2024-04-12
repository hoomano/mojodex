from datetime import datetime
import requests
import os
from app import server_socket, socketio_message_sender
from models.workflows.step_execution import WorkflowStepExecution
from models.workflows.workflow import Workflow

from models.produced_text_managers.workflow_produced_text_manager import WorkflowProducedTextManager
from mojodex_core.entities import MdUserTaskExecution, MdUserTask, MdWorkflowStep, MdTask, \
    MdUserWorkflowStepExecution
from mojodex_core.db import engine, Session
from typing import List
from mojodex_core.logging_handler import log_error
from sqlalchemy import case, and_

class WorkflowExecution:
    logger_prefix = "WorkflowExecution :: "

    def __del__(self):
        self.db_session.close()

    def __init__(self, workflow_execution_pk):
        try:
            self.db_session = Session(engine)
            self.db_object = self._get_db_object(workflow_execution_pk)
            self.user_id = self._db_user_workflow.user_id
            self.workflow = Workflow(self._db_workflow, self.db_session)
            self.past_accepted_steps_executions = [WorkflowStepExecution(self.db_session, db_past_accepted_step_execution, self.user_id) for
                                                   db_past_accepted_step_execution in self._db_past_accepted_step_executions]
            self._current_step = None
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

    def _get_db_object(self, workflow_execution_pk):
        try:
            db_workflow_execution = self.db_session.query(MdUserTaskExecution) \
                .filter(MdUserTaskExecution.user_task_execution_pk == workflow_execution_pk) \
                .first()
            return db_workflow_execution
        except Exception as e:
            raise Exception(f"_get_db_object :: {e}")
        
    @property
    def title(self):
        return self.db_object.title

    @property
    def _db_past_accepted_step_executions(self):
        try:
            return self.db_session.query(MdUserWorkflowStepExecution) \
                .join(MdWorkflowStep, MdUserWorkflowStepExecution.workflow_step_fk == MdWorkflowStep.workflow_step_pk) \
                .filter(
                    case(
                        # When `MdWorkflowStep.user_validation_required` is `True`, we check that `MdUserWorkflowStepExecution.validated` is also `True`
                        [
                            (MdWorkflowStep.user_validation_required == True, MdUserWorkflowStepExecution.validated == True),
                        ],
                        # if `user_validation_required` is `False`, we don't care about the `validated` status, and the `MdUserWorkflowStepExecution` will be included in the results regardless of its `validated` value.
                        else_=True
                    )
                ) \
                .filter(MdUserWorkflowStepExecution.user_task_execution_fk == self.db_object.user_task_execution_pk) \
                .filter(MdUserWorkflowStepExecution.error_status.is_(None)) \
                .order_by(MdUserWorkflowStepExecution.creation_date.asc()) \
                .all()

        except Exception as e:
            raise Exception(f"_db_step_executions :: {e}")

    def _generate_new_step_execution(self, step, parameter: dict):
        try:
            db_workflow_step_execution = MdUserWorkflowStepExecution(
                user_task_execution_fk=self.db_object.user_task_execution_pk,
                workflow_step_fk=step.workflow_step_pk,
                parameter=parameter
            )
            self.db_session.add(db_workflow_step_execution)
            self.db_session.commit()
            return WorkflowStepExecution(self.db_session, db_workflow_step_execution, self.user_id)
        except Exception as e:
            raise Exception(f"_generate_new_step_execution :: {e}")

    def _get_next_step_execution_to_run(self):
        try:
            print("🟠 _get_next_step_execution_to_run")
            if not self.past_accepted_steps_executions:  # no step validated yet
                self._current_step = self._generate_new_step_execution(self.workflow.db_steps[0],
                                                                       self.initial_parameters)  # of first step
                return self._current_step
            last_validated_step_execution = self.past_accepted_steps_executions[-1]
            if len(self.past_accepted_steps_executions) > 1:  # no dependency as it was the first step
                db_dependency_step = self.db_session.query(MdWorkflowStep) \
                    .join(MdUserTask, MdUserTask.task_fk == MdWorkflowStep.task_fk) \
                    .filter(MdUserTask.user_task_pk == self.db_object.user_task_fk) \
                    .filter(MdWorkflowStep.rank == last_validated_step_execution.workflow_step.rank - 1) \
                    .first()

                # find last execution of dependency step
                db_dependency_step_execution = self.db_session.query(MdUserWorkflowStepExecution) \
                    .filter(
                    MdUserWorkflowStepExecution.user_task_execution_fk == self.db_object.user_task_execution_pk) \
                    .filter(MdUserWorkflowStepExecution.workflow_step_fk == db_dependency_step.workflow_step_pk) \
                    .order_by(MdUserWorkflowStepExecution.creation_date.desc()) \
                    .first()

                # load all validated step executions of current step:
                current_step_executions_count = self.db_session.query(MdUserWorkflowStepExecution) \
                    .join(MdWorkflowStep, MdUserWorkflowStepExecution.workflow_step_fk == MdWorkflowStep.workflow_step_pk) \
                    .filter(
                    MdUserWorkflowStepExecution.user_task_execution_fk == self.db_object.user_task_execution_pk) \
                    .filter(
                    MdUserWorkflowStepExecution.workflow_step_fk == last_validated_step_execution.workflow_step.workflow_step_pk) \
                    .filter(
                        case(
                            # When `MdWorkflowStep.user_validation_required` is `True`, we check that `MdUserWorkflowStepExecution.validated` is also `True`
                            [
                                (MdWorkflowStep.user_validation_required == True, MdUserWorkflowStepExecution.validated == True),
                            ],
                            # if `user_validation_required` is `False`, we don't care about the `validated` status, and the `MdUserWorkflowStepExecution` will be included in the results regardless of its `validated` value.
                            else_=True
                        )) \
                    .filter(MdUserWorkflowStepExecution.error_status.is_(None)) \
                    .count()

                # have all parameters been executed and validated?
                if current_step_executions_count < len(db_dependency_step_execution.result):
                    current_parameter = db_dependency_step_execution.result[current_step_executions_count]
                    self._current_step = self._generate_new_step_execution(last_validated_step_execution.workflow_step,
                                                                           current_parameter)
                    return self._current_step

            # else, generate new step execution of next step
            next_step = self.db_session.query(MdWorkflowStep) \
                .join(MdUserTask, MdUserTask.task_fk == MdWorkflowStep.task_fk) \
                .filter(MdUserTask.user_task_pk == self.db_object.user_task_fk) \
                .filter(MdWorkflowStep.rank == last_validated_step_execution.workflow_step.rank + 1) \
                .first()
            # Reached last rank order => there is no next step
            if next_step is None:
                return None  # end of workflow
            # else
            self._current_step = self._generate_new_step_execution(next_step, last_validated_step_execution.result[0])
            return self._current_step
        except Exception as e:
            raise Exception(f"_get_current_step :: {e}")

    @property
    def initial_parameters(self):
        # self.json_inputs is [{"input_name": "<input_name>", "default_value": "<value>"}]'
        # initial_parameters is {"<input_name>": "<value>", ...}
        try:
            return {input["input_name"]: input["value"] for input in self.json_inputs}
        except Exception as e:
            raise Exception(f"initial_parameters :: {e}")

    @property
    def json_inputs(self):
        return self.db_object.json_input_values

    def __give_task_execution_title_and_summary(self, user_task_execution_pk):
        try:
            # call background backend /end_user_task_execution to update user task execution title and summary
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/user_task_execution_title_and_summary"
            pload = {'datetime': datetime.now().isoformat(),
                     'user_task_execution_pk': user_task_execution_pk}
            internal_request = requests.post(uri, json=pload)
            if internal_request.status_code != 200:
                log_error(
                    f"Error while calling background user_task_execution_title_and_summary : {internal_request.json()}")
        except Exception as e:
            print(f"🔴 __give_title_and_summary_task_execution :: {e}")

    def run(self):
        try:
            print("🟠 RUN")
            if not self.title:
                server_socket.start_background_task(self.__give_task_execution_title_and_summary,
                                                    self.db_object.user_task_execution_pk)
            next_step_execution_to_run = self._get_next_step_execution_to_run()
            if not next_step_execution_to_run:
                self.end_workflow_execution()
                return
            next_step_execution_to_run.execute(self.initial_parameters, self._past_validated_steps_results,
                                             self.db_object.session_id)

            self._send_ended_step_event()
            if not next_step_execution_to_run.workflow_step.user_validation_required and next_step_execution_to_run.error_status is None:
                # add previous step to past_accepted_steps_executions
                self.past_accepted_steps_executions.append(next_step_execution_to_run)
                self.run()
        except Exception as e:
            print(f"🔴 {self.logger_prefix} - run :: {e}")
            socketio_message_sender.send_error(f"Error during workflow run: {e}", self.db_object.session_id,
                                               user_task_execution_pk=self.db_object.user_task_execution_pk)

    def end_workflow_execution(self):
        try:
            produced_text, produced_text_version=self._generate_produced_text()
            server_socket.emit('workflow_execution_produced_text', {
                "user_task_execution_pk": self.db_object.user_task_execution_pk,
                "produced_text": produced_text_version.production,
                "produced_text_title": produced_text_version.title,
                "produced_text_pk": produced_text.produced_text_pk,
                "produced_text_version_pk": produced_text_version.produced_text_version_pk,
                "session_id": self.db_object.session_id
            }, to=self.db_object.session_id)
        except Exception as e:
            raise Exception(f"end_workflow_execution :: {e}")

    def _generate_produced_text(self):
        try:
            # concatenation of results of last step's validated executions
            last_step= self.workflow.db_steps[-1]
            validated_last_step_executions = self.db_session.query(MdUserWorkflowStepExecution) \
                .filter(
                MdUserWorkflowStepExecution.user_task_execution_fk == self.db_object.user_task_execution_pk) \
                .filter(
                MdUserWorkflowStepExecution.workflow_step_fk == last_step.workflow_step_pk) \
               .filter(
                    case(
                        # When `MdWorkflowStep.user_validation_required` is `True`, we check that `MdUserWorkflowStepExecution.validated` is also `True`
                        [
                            (MdWorkflowStep.user_validation_required == True, MdUserWorkflowStepExecution.validated == True),
                        ],
                        # if `user_validation_required` is `False`, we don't care about the `validated` status, and the `MdUserWorkflowStepExecution` will be included in the results regardless of its `validated` value.
                        else_=True
                    )
                ) \
                .filter(MdUserWorkflowStepExecution.error_status.is_(None)) \
                .order_by(MdUserWorkflowStepExecution.creation_date.desc())\
                .all()

            production = "\n\n".join([list(step.result[0].values())[0] for step in validated_last_step_executions[::-1]])

            produced_text_manager = WorkflowProducedTextManager(self.db_object.session_id, self.user_id,
                                                                self.db_object.user_task_execution_pk)
            produced_text, produced_text_version = produced_text_manager.save(production, text_type_pk=self.workflow.db_object.output_text_type_fk,)
            return produced_text, produced_text_version

        except Exception as e:
            raise Exception(f"_generate_produced_text :: {e}")

    @property
    def _past_validated_steps_results(self):
        try:
            return [{
                'step_name': step.name_for_system,
                'parameter': step.parameter,
                'result': step.result
            } for step in self.past_accepted_steps_executions]
        except Exception as e:
            raise Exception(f"_past_validated_steps_results :: {e}")

    def _send_ended_step_event(self):
        try:
            step_execution_json = self._current_step.to_json()
            step_execution_json["session_id"] = self.db_object.session_id
            server_socket.emit('workflow_step_execution_ended', step_execution_json, to=self.db_object.session_id)
        except Exception as e:
            raise Exception(f"_send_ended_step_event :: {e}")

    def get_step_execution_from_pk(self, step_execution_pk: int) -> WorkflowStepExecution:
        try:
            db_step_execution = self.db_session.query(MdUserWorkflowStepExecution) \
                .filter(MdUserWorkflowStepExecution.user_workflow_step_execution_pk == step_execution_pk) \
                .first()
            return WorkflowStepExecution(self.db_session, db_step_execution, self.user_id)
        except Exception as e:
            raise Exception(f"_last_step_execution :: {e}")

    def validate_step_execution(self, step_execution_pk: int):
        try:
            step_execution = self.get_step_execution_from_pk(step_execution_pk)
            step_execution.validate()
            self.past_accepted_steps_executions.append(step_execution)
        except Exception as e:
            raise Exception(f"validate_step_execution :: {e}")

    def _find_checkpoint_step(self):
        for step in reversed(self.past_accepted_steps_executions):
            if step.is_checkpoint:
                return step
        return None

    def _get_last_step_execution(self):
        try:
            db_step_execution = self.db_session.query(MdUserWorkflowStepExecution) \
                .filter(
                MdUserWorkflowStepExecution.user_task_execution_fk == self.db_object.user_task_execution_pk) \
                .order_by(MdUserWorkflowStepExecution.creation_date.desc()) \
                .first()
            if db_step_execution is None:
                return None
            return WorkflowStepExecution(self.db_session, db_step_execution, self.user_id)
        except Exception as e:
            raise Exception(f"_last_step_execution :: {e}")

    def invalidate_current_step(self, learned_instruction):
        try:
            current_step_in_validation = self._get_last_step_execution()
            current_step_in_validation.invalidate(self.db_object.session_id)
            if current_step_in_validation.workflow_step.is_checkpoint:
                current_step_in_validation.learn_instruction(learned_instruction)
                return

            # find checkpoint step
            checkpoint_step = self._find_checkpoint_step()
            # for all step in self.validated_steps_executions after checkpoint_step, invalidate them
            checkpoint_step_index = self.past_accepted_steps_executions.index(checkpoint_step)
            for validated_step in self.past_accepted_steps_executions[checkpoint_step_index:]:
                validated_step.invalidate(self.db_object.session_id)
                # remove from validated_steps_executions
                self.past_accepted_steps_executions.remove(validated_step)
            checkpoint_step.learn_instruction(learned_instruction)
        except Exception as e:
            raise Exception(f"invalidate_current_step :: {e}")

    @property
    def _db_workflow(self):
        try:
            return self.db_session.query(MdTask) \
                .join(MdUserTask, MdUserTask.task_fk == MdTask.task_pk) \
                .filter(MdUserTask.user_task_pk == self.db_object.user_task_fk) \
                .first()
        except Exception as e:
            raise Exception(f"_db_workflow :: {e}")

    @property
    def _db_user_workflow(self):
        try:
            return self.db_session.query(MdUserTask) \
                .filter(MdUserTask.user_task_pk == self.db_object.user_task_fk) \
                .first()
        except Exception as e:
            raise Exception(f"_db_user_workflow :: {e}")

    def get_before_checkpoint_validated_steps_executions(self, current_step_in_validation: WorkflowStepExecution) -> List[WorkflowStepExecution]:
        try:
            if current_step_in_validation.workflow_step.is_checkpoint:
                return self.past_accepted_steps_executions
            checkpoint_step = self._find_checkpoint_step()
            if not checkpoint_step:
                return []
            checkpoint_step_index = self.past_accepted_steps_executions.index(checkpoint_step)
            return self.past_accepted_steps_executions[:checkpoint_step_index]
        except Exception as e:
            raise Exception(f"before_checkpoint_steps_executions :: {e}")

    def get_after_checkpoint_validated_steps_executions(self, current_step_in_validation: WorkflowStepExecution) -> List[WorkflowStepExecution]:
        try:
            if current_step_in_validation.workflow_step.is_checkpoint:
                return []
            checkpoint_step = self._find_checkpoint_step()
            if not checkpoint_step:
                return self.past_accepted_steps_executions
            checkpoint_step_index = self.past_accepted_steps_executions.index(checkpoint_step)
            return self.past_accepted_steps_executions[checkpoint_step_index:]
        except Exception as e:
            raise Exception(f"after_checkpoint_to_current_steps_executions :: {e}")


    def get_steps_execution_json(self):
        try:
            validated_steps_json = [step_execution.to_json() for step_execution in self.past_accepted_steps_executions]
            last_step_execution = self._get_last_step_execution()
            if last_step_execution and last_step_execution.validated is None and last_step_execution.workflow_step.user_validation_required:
                validated_steps_json.append(last_step_execution.to_json())
            return validated_steps_json
        except Exception as e:
            raise Exception(f"{self.logger_prefix} get_steps_execution_json :: {e}")
