from abc import ABC, abstractmethod
from app import db
from models.workflows.run import WorkflowStepExecutionRun
from mojodex_core.entities import MdUserWorkflowStepExecution, MdUserWorkflowStepExecutionRun

class WorkflowStep(ABC):
    logger_prefix = "WorkflowStep :: "

    def __init__(self, workflow_step):
        try:
            self.db_object = workflow_step
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

    @property
    def workflow_step_pk(self):
        return self.db_object.workflow_step_pk

    @abstractmethod
    def execute(self, parameter, initial_parameters, history):
        pass

    @abstractmethod
    def concatenate_runs_results(self):
        pass

class WorkflowStepExecution:

    logger_prefix = "WorkflowStepExecution :: "
    def __init__(self, workflow_step, workflow_execution_pk):
        try:
            self.workflow_step = workflow_step
            self.db_object = self._get_or_create_db_object(self.workflow_step.workflow_step_pk, workflow_execution_pk)
            self.runs = [WorkflowStepExecutionRun(run) for run in self._db_runs]
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

  
    
    def _get_or_create_db_object(self, workflow_step_pk, workflow_execution_pk):
        try:
            # try to find it in db:
            db_workflow_step_execution = db.session.query(MdUserWorkflowStepExecution)\
                .filter(MdUserWorkflowStepExecution.user_workflow_execution_fk == workflow_execution_pk)\
                .filter(MdUserWorkflowStepExecution.workflow_step_fk == workflow_step_pk)\
                .order_by(MdUserWorkflowStepExecution.creation_date.desc()).first()
            if not db_workflow_step_execution:
                db_workflow_step_execution = MdUserWorkflowStepExecution(
                    user_workflow_execution_fk=workflow_execution_pk,
                    workflow_step_fk=workflow_step_pk
                )
                db.session.add(db_workflow_step_execution)
                db.session.commit()
            return db_workflow_step_execution
        except Exception as e:
            raise Exception(f"_get_or_create_db_object :: {e}")
        

    # getter initialized
    @property
    def initialized(self):
        return len(self.runs) > 0
    

    @property
    def _db_runs(self):
        return db.session.query(MdUserWorkflowStepExecutionRun)\
            .filter(MdUserWorkflowStepExecutionRun.user_workflow_step_execution_fk == self.db_object.user_workflow_step_execution_pk)\
            .order_by(MdUserWorkflowStepExecutionRun.creation_date.asc()).all()


    def initialize_runs(self, parameters):
        if not self.initialized:
            for parameter in parameters:
                # create run in db
                db_run = MdUserWorkflowStepExecutionRun(
                    md_user_workflow_step_execution_fk=self.db_object.md_user_workflow_step_execution_pk,
                    parameter=parameter
                )
                db.session.add(db_run)
                db.session.commit()
                self.runs.append(WorkflowStepExecutionRun(db_run))

            
    @property
    def validated(self):
        return all(run.validated for run in self.runs)

    def run(self, initial_parameters, history):
        # run from non-validated actions
        for run in self.runs:
            print(f"👉 Step run {run.parameter}")
            if not run.validated:
                return self.execute(run, initial_parameters, history)
            

    def execute(self, run, initial_parameters, history):
        result = self.workflow_step.execute(run.parameter, initial_parameters, history)
        run.result = result
        return run.result

    @property
    def result(self):
        return self.workflow_step.concatenate_runs_results([run.result for run in self.runs if run.validated])
    
    
    
    @property
    def current_run(self):
        for run in self.runs:
            if not run.validated:
                return run
            

    def to_json(self):
        try:
            return {
                "user_workflow_step_execution_pk": self.db_object.user_workflow_step_execution_pk,
                "workflow_step_pk": self.db_object.workflow_step_fk,
                "initialized": self.initialized,
                "validated": self.validated,
                "runs": [run.to_json() for run in self.runs],
                "result": self.result
            }
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: to_json :: {e}")
            