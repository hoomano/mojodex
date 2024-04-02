from app import server_socket
from models.workflows.step_execution import WorkflowStepExecution
from models.workflows.workflow import Workflow
from mojodex_core.entities import MdUserWorkflowExecution, MdUserWorkflow, MdWorkflowStep, MdWorkflow, \
    MdUserWorkflowStepExecution
from mojodex_core.db import engine, Session

class WorkflowExecution:
    logger_prefix = "WorkflowExecution :: "

    def __del__(self):
        self.db_session.close()

    def __init__(self, workflow_execution_pk):
        try:
            self.db_session = Session(engine)
            self.db_object = self._get_db_object(workflow_execution_pk)
            self.workflow = Workflow(self._db_workflow)
            self.user_id = self._db_user_workflow.user_id
            self.validated_steps_executions = [WorkflowStepExecution(self.db_session, db_validated_step_execution, self.user_id) for
                                               db_validated_step_execution in self._db_validated_step_executions]
            self._current_step = None
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

    def _get_db_object(self, workflow_execution_pk):
        try:
            db_workflow_execution = self.db_session.query(MdUserWorkflowExecution) \
                .filter(MdUserWorkflowExecution.user_workflow_execution_pk == workflow_execution_pk) \
                .first()
            return db_workflow_execution
        except Exception as e:
            raise Exception(f"_get_db_object :: {e}")

    @property
    def _db_workflow_steps(self):
        try:
            return self.db_session.query(MdWorkflowStep) \
                .join(MdUserWorkflow, MdUserWorkflow.workflow_fk == MdWorkflowStep.workflow_fk) \
                .filter(MdUserWorkflow.user_workflow_pk == self.db_object.user_workflow_fk) \
                .order_by(MdWorkflowStep.rank.asc()).all()
        except Exception as e:
            raise Exception(f"_db_workflow_steps :: {e}")

    @property
    def _db_validated_step_executions(self):
        try:
            return self.db_session.query(MdUserWorkflowStepExecution) \
                .filter(
                MdUserWorkflowStepExecution.user_workflow_execution_fk == self.db_object.user_workflow_execution_pk) \
                .filter(MdUserWorkflowStepExecution.validated == True) \
                .all()
        except Exception as e:
            raise Exception(f"_db_step_executions :: {e}")

    def _generate_new_step_execution(self, step, parameter: dict):
        try:
            db_workflow_step_execution = MdUserWorkflowStepExecution(
                user_workflow_execution_fk=self.db_object.user_workflow_execution_pk,
                workflow_step_fk=step.workflow_step_pk,
                parameter=parameter
            )
            self.db_session.add(db_workflow_step_execution)
            self.db_session.commit()
            return WorkflowStepExecution(self.db_session, db_workflow_step_execution, self.user_id)
        except Exception as e:
            raise Exception(f"_generate_new_step_execution :: {e}")

    def _get_current_step(self):
        try:
            if self._current_step:
                return self._current_step
            if not self.validated_steps_executions:  # no step validated yet
                self._current_step = self._generate_new_step_execution(self._db_workflow_steps[0],
                                                                       self.initial_parameters)  # of first step
                return self._current_step
            last_validated_step_execution = self.validated_steps_executions[-1]
            if len(self.validated_steps_executions) > 1:  # no dependency as it was the first step
                db_dependency_step = self.db_session.query(MdWorkflowStep) \
                    .join(MdUserWorkflow, MdUserWorkflow.workflow_fk == MdWorkflowStep.workflow_fk) \
                    .filter(MdUserWorkflow.user_workflow_pk == self.db_object.user_workflow_fk) \
                    .filter(MdWorkflowStep.rank == last_validated_step_execution.workflow_step.rank - 1) \
                    .first()

                # find last execution of dependency step
                db_dependency_step_execution = self.db_session.query(MdUserWorkflowStepExecution) \
                    .filter(
                    MdUserWorkflowStepExecution.user_workflow_execution_fk == self.db_object.user_workflow_execution_pk) \
                    .filter(MdUserWorkflowStepExecution.workflow_step_fk == db_dependency_step.workflow_step_pk) \
                    .order_by(MdUserWorkflowStepExecution.creation_date.desc()) \
                    .first()

                # load all validated step executions of current step:
                current_step_executions_count = self.db_session.query(MdUserWorkflowStepExecution) \
                    .filter(
                    MdUserWorkflowStepExecution.user_workflow_execution_fk == self.db_object.user_workflow_execution_pk) \
                    .filter(
                    MdUserWorkflowStepExecution.workflow_step_fk == last_validated_step_execution.workflow_step.workflow_step_pk) \
                    .filter(MdUserWorkflowStepExecution.validated == True) \
                    .order_by(MdUserWorkflowStepExecution.creation_date.desc()) \
                    .count()

                # have all parameters been executed and validated?
                if current_step_executions_count < len(db_dependency_step_execution.result):
                    current_parameter = db_dependency_step_execution.result[current_step_executions_count]
                    self._current_step = self._generate_new_step_execution(last_validated_step_execution.workflow_step,
                                                                           current_parameter)
                    return self._current_step

            # else, generate new step execution of next step
            next_step = self.db_session.query(MdWorkflowStep) \
                .join(MdUserWorkflow, MdUserWorkflow.workflow_fk == MdWorkflowStep.workflow_fk) \
                .filter(MdUserWorkflow.user_workflow_pk == self.db_object.user_workflow_fk) \
                .filter(MdWorkflowStep.rank == last_validated_step_execution.workflow_step.rank + 1) \
                .first()
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
        return self.db_object.json_inputs

    def run(self):
        try:
            if not self._get_current_step():
                return
            self._get_current_step().execute(self.initial_parameters, self._past_validated_steps_results,
                                             self.db_object.session_id)

            self._ask_for_validation()
        except Exception as e:
            # todo > Manage this error case
            print(f"🔴 {self.logger_prefix} - run :: {e}")
            raise Exception(f"run :: {e}")

    @property
    def _past_validated_steps_results(self):
        try:
            return [{
                'step_name': step.name,
                'parameter': step.parameter,
                'result': step.result
            } for step in self.validated_steps_executions]
        except Exception as e:
            raise Exception(f"_past_validated_steps_results :: {e}")

    def _ask_for_validation(self):
        try:
            step_execution_json = self._get_current_step().to_json()
            step_execution_json["session_id"] = self.db_object.session_id
            server_socket.emit('workflow_step_execution_ended', step_execution_json, to=self.db_object.session_id)
        except Exception as e:
            raise Exception(f"_ask_for_validation :: {e}")

    def get_step_execution_from_pk(self, step_execution_pk):
        try:
            db_step_execution = self.db_session.query(MdUserWorkflowStepExecution) \
                .filter(MdUserWorkflowStepExecution.user_workflow_step_execution_pk == step_execution_pk) \
                .first()
            return WorkflowStepExecution(self.db_session, db_step_execution, self.user_id)
        except Exception as e:
            raise Exception(f"_last_step_execution :: {e}")

    def validate_step_execution(self, step_execution_pk):
        try:
            step_execution = self.get_step_execution_from_pk(step_execution_pk)
            step_execution.validate()
            self.validated_steps_executions.append(step_execution)
        except Exception as e:
            raise Exception(f"validate_step_execution :: {e}")

    def _find_checkpoint_step(self):
        for step in reversed(self.validated_steps_executions):
            if step.is_checkpoint:
                return step
        return None

    def _get_last_step_execution(self):
        try:
            db_step_execution = self.db_session.query(MdUserWorkflowStepExecution) \
                .filter(
                MdUserWorkflowStepExecution.user_workflow_execution_fk == self.db_object.user_workflow_execution_pk) \
                .order_by(MdUserWorkflowStepExecution.creation_date.desc()) \
                .first()
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
            checkpoint_step_index = self.validated_steps_executions.index(checkpoint_step)
            for validated_step in self.validated_steps_executions[checkpoint_step_index:]:
                validated_step.invalidate(self.db_object.session_id)
                # remove from validated_steps_executions
                self.validated_steps_executions.remove(validated_step)
            checkpoint_step.learn_instruction(learned_instruction)
        except Exception as e:
            raise Exception(f"invalidate_current_step :: {e}")

    @property
    def _db_workflow(self):
        try:
            return self.db_session.query(MdWorkflow) \
                .join(MdUserWorkflow, MdUserWorkflow.workflow_fk == MdWorkflow.workflow_pk) \
                .filter(MdUserWorkflow.user_workflow_pk == self.db_object.user_workflow_fk) \
                .first()
        except Exception as e:
            raise Exception(f"_db_workflow :: {e}")

    @property
    def _db_user_workflow(self):
        try:
            return self.db_session.query(MdUserWorkflow) \
                .filter(MdUserWorkflow.user_workflow_pk == self.db_object.user_workflow_fk) \
                .first()
        except Exception as e:
            raise Exception(f"_db_user_workflow :: {e}")

    def get_before_checkpoint_validated_steps_executions(self, current_step_in_validation):
        try:
            if current_step_in_validation.workflow_step.is_checkpoint:
                return self.validated_steps_executions
            checkpoint_step = self._find_checkpoint_step()
            if not checkpoint_step:
                return []
            checkpoint_step_index = self.validated_steps_executions.index(checkpoint_step)
            return self.validated_steps_executions[:checkpoint_step_index]
        except Exception as e:
            raise Exception(f"before_checkpoint_steps_executions :: {e}")

    def get_after_checkpoint_validated_steps_executions(self, current_step_in_validation):
        try:
            if current_step_in_validation.workflow_step.is_checkpoint:
                return []
            checkpoint_step = self._find_checkpoint_step()
            if not checkpoint_step:
                return self.validated_steps_executions
            checkpoint_step_index = self.validated_steps_executions.index(checkpoint_step)
            return self.validated_steps_executions[checkpoint_step_index:]
        except Exception as e:
            raise Exception(f"after_checkpoint_to_current_steps_executions :: {e}")

    def to_json(self):
        try:
            return {
                "workflow_name": self.workflow.name,
                "user_workflow_execution_pk": self.db_object.user_workflow_execution_pk,
                "user_workflow_fk": self.db_object.user_workflow_fk,
                "steps": [{'workflow_step_pk': step.workflow_step_pk, 'step_name': step.name} for step in
                          self._db_workflow_steps],
                "validated_steps_executions": [step_execution.to_json() for step_execution in
                                               self.validated_steps_executions],
                "session_id": self.db_object.session_id,
                "inputs": self.json_inputs
            }
        except Exception as e:
            raise Exception(f"{self.logger_prefix} to_json :: {e}")
