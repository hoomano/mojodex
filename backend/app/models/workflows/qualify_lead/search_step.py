from models.workflows.step import WorkflowStep
from typing import List
        

class SearchStep(WorkflowStep):

    @property
    def description(self):
        return "Search a query on Search Engine and make a summary out of it."

    def __init__(self, workflow_step):
        super().__init__(workflow_step, input_keys=['query', 'gl', 'hl'], output_keys=['results', 'summary'])

    
    def _execute(self, parameter: dict, initial_parameter: dict, history: List[dict]):
        try: 
            # input keys: company
            
            
            return [{'results': f"Results of search for query {parameter['query']}",
                     'summary': f"Summary of search for query {parameter['query']}"}]
        
            # output keys: 'query', 'gl', 'hl'
        except Exception as e:
            raise Exception(f"execute :: {e}")
