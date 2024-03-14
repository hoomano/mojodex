from abc import ABC, abstractmethod
from app import db
from models.workflows.step import WorkflowStep, WorkflowStepExecution
from mojodex_core.entities import MdUserWorkflowExecution, MdUserWorkflow, MdWorkflowStep, MdWorkflow
from models.workflows.steps_library import steps_class
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
        return self.db_object.initial_parameters

    def run(self):
        step_execution_to_run = self._current_step_execution
        print(f"🟢 Running step: {step_execution_to_run.name} - parameters: {self.intermediate_results[-1] if self.intermediate_results else [self.initial_parameters]} ")
        step_execution_to_run.initialize_runs(self.intermediate_results[-1] if self.intermediate_results else [self.initial_parameters])
        result = step_execution_to_run.run(self.initial_parameters, self.intermediate_results)
        self._ask_for_validation(result)
        

    @property
    def _current_step_execution(self):
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


    @property
    def intermediate_results(self):
        return [step.result for step in self.steps[:-1] if step.initialized]

    def _ask_for_validation(self, result):
        print(f"---- ASK FOR VALIDATION ----\n{result}\n ------ END -----")
        
    def handle_user_feedback(self, user_feedback=True):
        if user_feedback:
            self._validate()
        else:
            self._invalidate()
        self.run()

    def _validate(self):
        self._current_step_execution.current_run.validate()

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
                "steps": [step_execution.to_json() for step_execution in self.steps_executions]
            }
        except Exception as e:
            raise Exception(f"{logger_prefix} to_json :: {e}")



