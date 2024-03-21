from app import db


class WorkflowStepExecutionRun:
    logger_prefix = "WorkflowStepExecutionRun :: "

    def __init__(self, db_object_run=None):
        try:
            self.db_object_run=db_object_run
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

    @property
    def validated(self):
        return self.db_object_run.validated
    
    @validated.setter
    def validated(self, value):
        self.db_object_run.validated = value
        db.session.commit()
    
    @property
    def parameter(self):
        return self.db_object_run.parameter
    
    
    @property
    def result(self):
        return self.db_object_run.result
    
    @result.setter
    def result(self, value):
        self.db_object_run.result = value
        db.session.commit()

    def to_json(self):
        return {
            "workflow_step_execution_run_pk": self.db_object_run.workflow_step_execution_run_pk,
            "parameter": self.db_object_run.parameter,
            "validated": self.db_object_run.validated,
            "result": self.db_object_run.result
        }
        