from app import db, server_socket
from models.workflows.step import WorkflowStepExecution
from mojodex_core.entities import MdUserWorkflowExecution, MdUserWorkflow, MdWorkflowStep, MdWorkflow
from models.workflows.steps_library import steps_class
from sqlalchemy.orm.attributes import flag_modified
# DB schema:
# MdUser: user_id
# MdWorkflow: workflow_pk, name
# MdWorkflowStep: workflow_step_pk, name, workflow_fk
# MdUserWorkflow: user_workflow_pk, user_id, workflow_fk
# MdUserWorkflowExecution: user_workflow_execution_pk, user_workflow_fk
# MdUserWorkflowStepExecution: user_workflow_step_execution_pk, user_workflow_execution_fk, user_workflow_step_fk
# MdUserWorkflowStepExecutionRun: md_user_workflow_step_execution_run_pk, md_user_workflow_step_execution_fk, validated, result


class WorkflowExecution:
    logger_prefix = "WorkflowExecution :: "

    def __init__(self, workflow_execution_pk):
        try:
            self.db_object = self._get_db_object(workflow_execution_pk)
            self.steps_executions = [WorkflowStepExecution(steps_class[db_workflow_step.name](db_workflow_step), workflow_execution_pk) for db_workflow_step in self._db_workflow_steps]
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")


    def _get_db_object(self, workflow_execution_pk):
        try:
            db_workflow_execution = db.session.query(MdUserWorkflowExecution)\
                .filter(MdUserWorkflowExecution.user_workflow_execution_pk == workflow_execution_pk)\
                .first()
            return db_workflow_execution
        except Exception as e:
            raise Exception(f"_get_db_object :: {e}")
    

    @property
    def _db_workflow_steps(self):
        try:
            return db.session.query(MdWorkflowStep)\
                .join(MdUserWorkflow, MdUserWorkflow.workflow_fk == MdWorkflowStep.workflow_fk)\
                .filter(MdUserWorkflow.user_workflow_pk == self.db_object.user_workflow_fk)\
                .order_by(MdWorkflowStep.workflow_step_pk.asc()).all()
        except Exception as e:
            raise Exception(f"_db_workflow_steps :: {e}")

    @property
    def initial_parameters(self):
        #return self.db_object.json_input
        return self.db_object.json_input

    @initial_parameters.setter
    def initial_parameters(self, value):
        try:
            self.db_object.json_input = value
            flag_modified(self.db_object, "json_input")
            db.session.commit()
        except Exception as e:
            raise Exception(f"initial_parameters :: {e}")

    def run(self):
        try:
            step_execution_to_run = self._current_step_execution
            if not step_execution_to_run:
                return
            print(f"🟢 Running step: {step_execution_to_run.name} - parameters: {self._intermediate_results[-1] if self._intermediate_results else [self.initial_parameters]} ")
            step_execution_to_run.initialize_runs(self._intermediate_results[-1] if self._intermediate_results else [self.initial_parameters], self.db_object.session_id)
            
            step_execution_to_run.run(self.initial_parameters, self._intermediate_results, self.db_object.session_id)
            self._ask_for_validation()
        except Exception as e:
            print(f"🔴 {self.logger_prefix} - run :: {e}")
            raise Exception(f"run :: {e}")
        

    @property
    def _current_step_execution(self):
        try:
            # step to run is:
            # last one initialized which runs are not all validated
            # or first step not initialized
            # browse steps backwards
            for step_execution in reversed(self.steps_executions):
                if step_execution.initialized and not step_execution.validated:
                    return step_execution
            # else, next step to run is the first one not initialized
            for step_execution in self.steps_executions:
                if not step_execution.initialized:
                    return step_execution
            return None
        except Exception as e:
            raise Exception(f"_current_step_execution :: {e}")


    @property
    def _intermediate_results(self):
        try:
            return [step.result for step in self.steps_executions[:-1] if step.initialized]
        except Exception as e:
            raise Exception(f"_intermediate_results :: {e}")

    def _ask_for_validation(self):
        try:
            run_json = self._current_step_execution.current_run.to_json()
            run_json["session_id"] = self.db_object.session_id
            run_json["step_execution_fk"] = self._current_step_execution.db_object.user_workflow_step_execution_pk
            server_socket.emit('workflow_run_ended', run_json, to=self.db_object.session_id)
        except Exception as e:
            raise Exception(f"_ask_for_validation :: {e}")

    def validate_current_run(self):
        try:
            self._current_step_execution.current_run.validate()
        except Exception as e:
            raise Exception(f"validate_current_run :: {e}")

    def _find_checkpoint_step(self):
        for step in reversed(self.steps):
            if step.initialized and step.checkpoint:
                return step
        return None

    def _invalidate(self):
        # find checkpoint step
        checkpoint_step = self._find_checkpoint_step()
        # if there are other steps after checkpoint, reset them
        if not checkpoint_step:
            for step in self.steps:
                step.reset()
        else:
            # reset steps after checkpoint
            checkpoint_step_index = self.steps.index(checkpoint_step)
            for step in self.steps[checkpoint_step_index+1:]:
                step.reset()

    @property
    def _db_workflow(self):
        try:
            return db.session.query(MdWorkflow)\
                .join(MdUserWorkflow, MdUserWorkflow.workflow_fk == MdWorkflow.workflow_pk)\
                .filter(MdUserWorkflow.user_workflow_pk == self.db_object.user_workflow_fk)\
                .first()
        except Exception as e:
            raise Exception(f"_db_workflow :: {e}")

    def to_json(self):
        try:
            return {
                "workflow_name": self._db_workflow.name,
                "user_workflow_execution_pk": self.db_object.user_workflow_execution_pk,
                "user_workflow_fk": self.db_object.user_workflow_fk,
                "steps": [step_execution.to_json() for step_execution in self.steps_executions],
                "session_id": self.db_object.session_id
            }
        except Exception as e:
            raise Exception(f"{self.logger_prefix} to_json :: {e}")



