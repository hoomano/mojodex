from models.workflows.step import WorkflowStep
from typing import List
        

class SearchStep(WorkflowStep):


    @property
    def description(self):
        return "Search a query on Search Engine and make a summary out of it."

    @property
    def is_checkpoint(self):
        return False

    @property
    def input_keys(self):
        return ['query', 'gl', 'hl']
    
    @property
    def output_keys(self):
        return ['results', 'summary']
    
    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict, history: List[dict]):
        try: 
            # input keys: company
            
            
            return [{'results': f"Results of search for query {parameter['query']}",
                     'summary': f"Summary of search for query {parameter['query']}"}]
        
            # output keys: 'query', 'gl', 'hl'
        except Exception as e:
            raise Exception(f"execute :: {e}")
