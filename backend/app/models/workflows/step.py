from abc import ABC, abstractmethod
from typing import List


class WorkflowStep(ABC):
    logger_prefix = "WorkflowStep :: "

    def __init__(self, workflow_step):
        try:
            self.db_object = workflow_step
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def input_keys(self) -> List[str]:
        raise NotImplementedError
        
    @property
    @abstractmethod
    def output_keys(self) -> List[str]:
        raise NotImplementedError

    @property
    def workflow_step_pk(self) -> int:
        return self.db_object.workflow_step_pk
    
    @property
    def is_checkpoint(self):
        return True
    
    @property
    def rank(self):
        return self.db_object.rank
    
    @abstractmethod
    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameters: dict, past_validated_steps_results: List[dict]):
       pass

    
    def execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict, past_validated_steps_results: List[dict]):
        """
        Returns a list of parameters (dict)
        """
        try:
            
            # ensure that input keys are present in parameter
            for key in self.input_keys:
                if key not in parameter:
                    raise Exception(f"execute :: key {key} not in parameter")
            output = self._execute(parameter, learned_instructions, initial_parameter, past_validated_steps_results) # list of dict
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


