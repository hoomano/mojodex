from abc import ABC, abstractmethod
import json
from app import server_socket
from models.workflows.run import WorkflowStepExecutionRun
from mojodex_core.entities import MdUserWorkflowStepExecution, MdUserWorkflowStepExecutionRun
from typing import List
import time
class WorkflowStep(ABC):
    logger_prefix = "WorkflowStep :: "

    @property
    @abstractmethod
    def description(self):
        pass

    def __init__(self, workflow_step, input_keys: List[str], output_keys: List[str]):
        try:
            self.input_keys = input_keys
            self.output_keys = output_keys
            self.db_object = workflow_step
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

    @property
    def workflow_step_pk(self):
        return self.db_object.workflow_step_pk
    
    @property
    def is_checkpoint(self):
        return self.db_object.is_checkpoint
    
    @abstractmethod
    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameters: dict, history: List[dict], workflow_conversation: str):
       pass

    
    def execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict, history: List[dict], workflow_conversation: str):
        """
        Returns a list of parameters (dict)
        """
        try:
            
            # ensure that input keys are present in parameter
            for key in self.input_keys:
                if key not in parameter:
                    raise Exception(f"execute :: key {key} not in parameter")
            output = self._execute(parameter, learned_instructions, initial_parameter, history, workflow_conversation) # list of dict
            # ensure output is a list
            if not isinstance(output, List):
                raise Exception(f"execute :: output is not a list")
            # ensure that output keys are present in output
            for item in output:
                if not isinstance(item, dict):
                    raise Exception(f"execute :: output item {item} is not a dict")
                for key in self.output_keys:
                    if key not in item:
                        raise Exception(f"execute :: key {key} not in output")
            return output
        except Exception as e:
            raise Exception(f"{WorkflowStep.logger_prefix} execute :: {e}")


class WorkflowStepExecution:

    logger_prefix = "WorkflowStepExecution :: "
    def __init__(self, db_session, workflow_step, workflow_execution_pk):
        try:
            self.db_session = db_session
            self.workflow_step = workflow_step
            self.db_object = self._get_or_create_db_object(self.workflow_step.workflow_step_pk, workflow_execution_pk)
            self.runs = [WorkflowStepExecutionRun(self.db_session, run) for run in self._db_runs]
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

    def _get_db_object(self, workflow_step_pk, workflow_execution_pk):
        try:
            db_workflow_step_execution = self.db_session.query(MdUserWorkflowStepExecution)\
                .filter(MdUserWorkflowStepExecution.user_workflow_execution_fk == workflow_execution_pk)\
                .filter(MdUserWorkflowStepExecution.workflow_step_fk == workflow_step_pk)\
                .order_by(MdUserWorkflowStepExecution.creation_date.desc()).first()
            return db_workflow_step_execution
        except Exception as e:
            raise Exception(f"_get_db_object :: {e}")
        
    def _create_db_object(self, workflow_step_pk, workflow_execution_pk):
        try:
            db_workflow_step_execution = MdUserWorkflowStepExecution(
                user_workflow_execution_fk=workflow_execution_pk,
                workflow_step_fk=workflow_step_pk
            )
            self.db_session.add(db_workflow_step_execution)
            self.db_session.commit()
            return db_workflow_step_execution
        except Exception as e:
            raise Exception(f"_create_db_object :: {e}")
    
    def _get_or_create_db_object(self, workflow_step_pk, workflow_execution_pk):
        try:
            # try to find it in db:
            db_workflow_step_execution = self._get_db_object(workflow_step_pk, workflow_execution_pk)
            if not db_workflow_step_execution:
                db_workflow_step_execution = self._create_db_object(workflow_step_pk, workflow_execution_pk)
            return db_workflow_step_execution
        except Exception as e:
            raise Exception(f"_get_or_create_db_object :: {e}")
        
    def reset(self, session_id: str):
        try:
            previous_step_execution_pk = self.db_object.user_workflow_step_execution_pk
            db_workflow_step_execution = self._create_db_object(self.workflow_step.workflow_step_pk, self.db_object.user_workflow_execution_fk)
            self.db_object = db_workflow_step_execution
            self.runs = []
            step_json = self.to_json()
            # add session_id to step_json
            step_json["session_id"] = session_id
            step_json["previous_step_execution_pk"] = previous_step_execution_pk
            server_socket.emit('workflow_step_execution_reset', step_json, to=session_id)
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: reset :: {e}")



    # getter initialized
    @property
    def initialized(self):
        try:
            return len(self.runs) > 0
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: initialized :: {e}")
    
    @property
    def is_checkpoint(self):
        return self.workflow_step.is_checkpoint

    @property
    def _db_runs(self):
        return self.db_session.query(MdUserWorkflowStepExecutionRun)\
            .filter(MdUserWorkflowStepExecutionRun.user_workflow_step_execution_fk == self.db_object.user_workflow_step_execution_pk)\
            .order_by(MdUserWorkflowStepExecutionRun.creation_date.asc()).all()


    def initialize_runs(self, parameters: List[dict], session_id: str):
        try:
            if not self.initialized:
                for parameter in parameters:
                    # if parameter is a dict, encode json to string
                    if isinstance(parameter, dict) or isinstance(parameter, List):
                        parameter = json.dumps(parameter)
                    else:
                        parameter = str(parameter)
                    # create run in db
                    db_run = MdUserWorkflowStepExecutionRun(
                        user_workflow_step_execution_fk=self.db_object.user_workflow_step_execution_pk,
                        parameter=parameter
                    )
                    self.db_session.add(db_run)
                    self.db_session.commit()
                    self.runs.append(WorkflowStepExecutionRun(self.db_session, db_run))
                step_json = self.to_json()
                # add session_id to step_json
                step_json["session_id"] = session_id
                server_socket.emit('workflow_step_execution_initialized', step_json, to=session_id)
                
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: initialize_runs :: {e}")

            
    @property
    def validated(self):
        return self.initialized and all(run.validated for run in self.runs)

    def run(self, initial_parameter: dict, history: List[dict], session_id: str, workflow_conversation: str):
        try:
            # run from non-validated actions
            for run in self.runs:
                if not run.validated:
                    # create an execution for the run
                    run.prepare_execution() # This creates a run_execution in db
                    run_json = run.to_json()
                    run_json["session_id"] = session_id
                    run_json["step_execution_fk"] = self.db_object.user_workflow_step_execution_pk
                    server_socket.emit('workflow_run_started', run_json, to=session_id)
                    return self.execute(run, initial_parameter, history, workflow_conversation)
            return None
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: run :: {e}")
            

    def execute(self, run: WorkflowStepExecutionRun, initial_parameter: dict, history: List[dict], workflow_conversation: str):
        try:
            result = self.workflow_step.execute(run.parameter, run.learned_instructions, initial_parameter, history, workflow_conversation)
            run.result = result
            return run.result
        except Exception as e:
            raise Exception(f"execute :: {e}")

    @property
    def history(self):
        if not self.result:
            return []
        return[{'step_name': self.name, 
                'parameter': run.parameter,
                'result': run.result} for run in self.runs if run.validated]
                
                

    @property
    def result(self):
        if not self.initialized:
            return None
        result = []
        for run in self.runs:
            if run.validated:
                result += run.result
        return result
                
    
    @property
    def name(self):
        return self.workflow_step.db_object.name
    
    @property
    def description(self):
        return self.workflow_step.description
    
    @property
    def current_run(self):
        for run in self.runs:
            if not run.validated:
                return run
            
    @property
    def last_run(self):
        if self.initialized:
            return self.runs[-1]
        return None
            
    def invalidate_last_run(self):
        try:
            if self.initialized:
                self.runs[-1].invalidate()
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: invalidate_last_run :: {e}")

    def to_json(self):
        try:
            return {
                "user_workflow_step_execution_pk": self.db_object.user_workflow_step_execution_pk,
                "workflow_step_pk": self.db_object.workflow_step_fk,
                "step_name": self.name,
                "initialized": self.initialized,
                "validated": self.validated,
                "runs": [run.to_json() for run in self.runs],
                "result": self.result
            }
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: to_json :: {e}")
            