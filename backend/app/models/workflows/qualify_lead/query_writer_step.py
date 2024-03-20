from models.workflows.step import WorkflowStep
from typing import List
        

class QueryWriterStep(WorkflowStep):

    @property
    def description(self):
        return "Write the query to search for the company industry."

    def __init__(self, workflow_step):
        super().__init__(workflow_step, input_keys=['company'], output_keys=['query', 'gl', 'hl'])

    
    def _execute(self, parameter: dict, initial_parameter: dict, history: List[dict]):
        try: 
            # input keys: company
        
            return [{'query': f"{parameter['company']} industry", 'gl': 'US', 'hl': 'en'}]
        
            # output keys: 'query', 'gl', 'hl'
        except Exception as e:
            raise Exception(f"execute :: {e}")
