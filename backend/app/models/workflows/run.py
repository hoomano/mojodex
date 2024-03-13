from app import db


class WorkflowStepExecutionRun:

    def __init__(self, db_object_run=None):
        self.db_object_run=  db_object_run

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
        