from app import server_socket
from models.workflows.step import WorkflowStepExecution
from mojodex_core.entities import MdUserWorkflowExecution, MdUserWorkflow, MdWorkflowStep, MdWorkflow
from models.workflows.steps_library import steps_class
from sqlalchemy.orm.attributes import flag_modified
from mojodex_core.db import MySession
# DB schema:
# MdUser: user_id
# MdWorkflow: workflow_pk, name
# MdWorkflowStep: workflow_step_pk, name, workflow_fk
# MdUserWorkflow: user_workflow_pk, user_id, workflow_fk
# MdUserWorkflowExecution: user_workflow_execution_pk, user_workflow_fk
# MdUserWorkflowStepExecution: user_workflow_step_execution_pk, user_workflow_execution_fk, user_workflow_step_fk
# MdUserWorkflowStepExecutionRun: md_user_workflow_step_execution_run_pk, md_user_workflow_step_execution_fk, validated, result

class Workflow:
    def __init__(self, db_object):
        self.db_object = db_object

    @property
    def name(self):
        return self.db_object.name
    
    @property
    def description(self):
        return self.db_object.description

    

class WorkflowExecution:
    logger_prefix = "WorkflowExecution :: "

    def __del__(self):
        self.db_session.close()

    def __init__(self, workflow_execution_pk):
        try:
            self.db_session = MySession()
            self.db_object = self._get_db_object(workflow_execution_pk)
            self.workflow = Workflow(self._db_workflow)
            self.steps_executions = [WorkflowStepExecution(self.db_session, steps_class[db_workflow_step.name](db_workflow_step), workflow_execution_pk) for db_workflow_step in self._db_workflow_steps]
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")


    def _get_db_object(self, workflow_execution_pk):
        try:
            db_workflow_execution = self.db_session.query(MdUserWorkflowExecution)\
                .filter(MdUserWorkflowExecution.user_workflow_execution_pk == workflow_execution_pk)\
                .first()
            return db_workflow_execution
        except Exception as e:
            raise Exception(f"_get_db_object :: {e}")
    

    @property
    def _db_workflow_steps(self):
        try:
            return self.db_session.query(MdWorkflowStep)\
                .join(MdUserWorkflow, MdUserWorkflow.workflow_fk == MdWorkflowStep.workflow_fk)\
                .filter(MdUserWorkflow.user_workflow_pk == self.db_object.user_workflow_fk)\
                .order_by(MdWorkflowStep.workflow_step_pk.asc()).all()
        except Exception as e:
            raise Exception(f"_db_workflow_steps :: {e}")

    @property
    def initial_parameters(self):
        # self.json_inputs is [{"input_name": "<input_name>", "default_value": "<value>"}]'
        # initial_parameters is {"<input_name>": "<value>", ...}
        try:
            return {input["input_name"]: input["default_value"] for input in self.json_inputs}
        except Exception as e:
            raise Exception(f"initial_parameters :: {e}")

    @property
    def json_inputs(self):
        return self.db_object.json_inputs

    def run(self):
        try:
            step_execution_to_run = self.current_step_execution
            if not step_execution_to_run:
                return
            step_execution_to_run.initialize_runs(self._intermediate_results[-1] if self._intermediate_results else [self.initial_parameters], self.db_object.session_id)
            
            step_execution_to_run.run(self.initial_parameters, self._intermediate_results, self.db_object.session_id)
            self._ask_for_validation()
        except Exception as e:
            print(f"🔴 {self.logger_prefix} - run :: {e}")
            raise Exception(f"run :: {e}")
        

    @property
    def current_step_execution(self):
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
            run_json = self.current_step_execution.current_run.to_json()
            run_json["session_id"] = self.db_object.session_id
            run_json["step_execution_fk"] = self.current_step_execution.db_object.user_workflow_step_execution_pk
            server_socket.emit('workflow_run_ended', run_json, to=self.db_object.session_id)
        except Exception as e:
            raise Exception(f"_ask_for_validation :: {e}")

    def validate_current_run(self):
        try:
            self.current_step_execution.current_run.validate()
        except Exception as e:
            raise Exception(f"validate_current_run :: {e}")

    def _find_checkpoint_step(self):
        for step in reversed(self.steps_executions):
            if step.initialized and step.is_checkpoint:
                return step
        return None

    def invalidate_current_run(self):
        # find checkpoint step
        checkpoint_step = self._find_checkpoint_step()
        # if there are other steps after checkpoint, reset them
        if not checkpoint_step:
            print("🔴 no checkpoint found")
            for step in self.steps_executions:
                step.reset(self.db_object.session_id)
        else:
            print(f"🟢 checkpoint step is: {checkpoint_step.name}")
            # reset steps after checkpoint
            checkpoint_step_index = self.steps_executions.index(checkpoint_step)
            print(f"🟢 checkpoint step index is: {checkpoint_step_index}")
            for step in self.steps_executions[checkpoint_step_index+1:]:
                if step.initialized:
                    print(f"🟢 Resetting step: {step.name}")
                    step.reset(self.db_object.session_id)
            checkpoint_step.invalidate_last_run()

    @property
    def _db_workflow(self):
        try:
            return self.db_session.query(MdWorkflow)\
                .join(MdUserWorkflow, MdUserWorkflow.workflow_fk == MdWorkflow.workflow_pk)\
                .filter(MdUserWorkflow.user_workflow_pk == self.db_object.user_workflow_fk)\
                .first()
        except Exception as e:
            raise Exception(f"_db_workflow :: {e}")


    @property
    def before_checkpoint_steps_executions(self):
        try:
            checkpoint_step = self._find_checkpoint_step()
            if not checkpoint_step:
                return []
            checkpoint_step_index = self.steps_executions.index(checkpoint_step)
            return self.steps_executions[:checkpoint_step_index]
        except Exception as e:
            raise Exception(f"before_checkpoint_steps_executions :: {e}")
        

    @property
    def after_checkpoint_to_current_steps_executions(self):
        try:
            checkpoint_step = self._find_checkpoint_step()
            if not checkpoint_step:
                return self.steps_executions
            checkpoint_step_index = self.steps_executions.index(checkpoint_step)
            print(f"🟢 checkpoint_step_index: {checkpoint_step_index}")
            return self.steps_executions[checkpoint_step_index:]
        except Exception as e:
            raise Exception(f"after_checkpoint_to_current_steps_executions :: {e}")

    def to_json(self):
        try:
            return {
                "workflow_name": self.workflow.name,
                "user_workflow_execution_pk": self.db_object.user_workflow_execution_pk,
                "user_workflow_fk": self.db_object.user_workflow_fk,
                "steps": [step_execution.to_json() for step_execution in self.steps_executions],
                "session_id": self.db_object.session_id,
                "inputs": self.json_inputs
            }
        except Exception as e:
            raise Exception(f"{self.logger_prefix} to_json :: {e}")



