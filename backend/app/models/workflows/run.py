import json

class WorkflowStepExecutionRun:
    logger_prefix = "WorkflowStepExecutionRun :: "

    def __init__(self, db_session, db_object_run):
        try:
            self.db_session = db_session
            self.db_object_run=db_object_run
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

    @property
    def validated(self):
        return self.db_object_run.validated
    
    @validated.setter
    def validated(self, value):
        self.db_object_run.validated = value
        self.db_session.commit()

    def validate(self):
        self.validated = True
    
    @property
    def parameter(self):
        try:
            value = self.db_object_run.parameter
            return json.loads(value) if value else None
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: parameter :: {e}")
    
    
    @property
    def result(self):
        string_value = self.db_object_run.result
        return json.loads(string_value) if string_value else None
    
    @result.setter
    def result(self, value):
        if isinstance(value, dict) or isinstance(value, list):
            value = json.dumps(value)
        else:
            value = str(value)
        self.db_object_run.result = value
        self.db_session.commit()

    def to_json(self):
        try: 
            return {
                "user_workflow_step_execution_run_pk": self.db_object_run.user_workflow_step_execution_run_pk,
                "parameter": self.parameter,
                "validated": self.db_object_run.validated,
                "result": self.result
            }
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: to_json :: {e}")
        