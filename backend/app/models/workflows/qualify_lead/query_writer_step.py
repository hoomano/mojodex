from models.workflows.step import WorkflowStep
from typing import List
        

class QueryWriterStep(WorkflowStep):


    @property
    def description(self):
        return "Write the query to search for the company industry."

    @property
    def input_keys(self):
        return ['company']
    
    @property
    def output_keys(self):
        return ['query', 'gl', 'hl']
    
    
    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict, history: List[dict]):
        try: 
            # input keys: company
        
            return [{'query': f"{parameter['company']} industry", 'gl': 'US', 'hl': 'en'}]
        
            # output keys: 'query', 'gl', 'hl'
        except Exception as e:
            raise Exception(f"execute :: {e}")
