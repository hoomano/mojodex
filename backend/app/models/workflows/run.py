import json
from mojodex_core.entities import MdUserWorkflowStepExecutionRunExecution

class WorkflowStepExecutionRunExecution:
    def __init__(self, db_session, db_object):
        self.db_session = db_session
        self.db_object = db_object

    @property
    def result(self):
        string_value = self.db_object.result
        return json.loads(string_value) if string_value else None
    
    @result.setter
    def result(self, value):
        if isinstance(value, dict) or isinstance(value, list):
            value = json.dumps(value)
        else:
            value = str(value)
        self.db_object.result = value
        self.db_session.commit()


class WorkflowStepExecutionRun:
    logger_prefix = "WorkflowStepExecutionRun :: "

    def __init__(self, db_session, db_object_run):
        try:
            self.db_session = db_session
            self.db_object_run=db_object_run
            self.current_execution = self._get_execution()
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

    def _get_execution(self):
        try:
            run_execution_db = self.db_session.query(MdUserWorkflowStepExecutionRunExecution)\
                .filter(MdUserWorkflowStepExecutionRunExecution.user_workflow_step_execution_run_fk == self.db_object_run.user_workflow_step_execution_run_pk)\
                .order_by(MdUserWorkflowStepExecutionRunExecution.creation_date.desc()).first()
            if not run_execution_db:
                return None
            return WorkflowStepExecutionRunExecution(self.db_session, run_execution_db)
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: _get_execution :: {e}")

    def prepare_execution(self):
        try:
            run_execution_db = MdUserWorkflowStepExecutionRunExecution(
                user_workflow_step_execution_run_fk=self.db_object_run.user_workflow_step_execution_run_pk
            )
            self.db_session.add(run_execution_db)
            self.db_session.commit()
            self.current_execution = WorkflowStepExecutionRunExecution(self.db_session, run_execution_db)
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: prepare_execution :: {e}")

    @property
    def validated(self):
        return self.db_object_run.validated
    
    @validated.setter
    def validated(self, value):
        self.db_object_run.validated = value
        self.db_session.commit()

    def validate(self):
        self.validated = True

    def invalidate(self):
        self.validated = False
    
    @property
    def parameter(self):
        try:
            value = self.db_object_run.parameter
            return json.loads(value) if value else None
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: parameter :: {e}")
    
    @property
    def result(self):
        return self.current_execution.result if self.current_execution else None
    
    @result.setter
    def result(self, value):
        try:
            self.current_execution.result = value
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: result :: {e}")
    

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
        