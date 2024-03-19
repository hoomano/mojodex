from models.workflows.step import WorkflowStep
import json
from typing import List
        

class SectionsDividerStep(WorkflowStep):

    def __init__(self, workflow_step):
        super().__init__(workflow_step, input_keys=['text'], output_keys=['section'])

    
    def _execute(self, parameter: dict, initial_parameter: dict, history: List[dict]):
        try: 
            # input keys: text
            
            sections=parameter['text'].split("\n")
            return [{'section': section} for section in sections]
        
            # output keys: 'section'
        except Exception as e:
            raise Exception(f"execute :: {e}")
