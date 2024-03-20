from models.workflows.step import WorkflowStep
import json
from typing import List
        

class StanzaWriterStep(WorkflowStep):

    @property
    def description(self):
        return "Write a stanza."

    def __init__(self, workflow_step):
        super().__init__(workflow_step, input_keys=['stanza_theme'], output_keys=['stanza'])

    
    def _execute(self, parameter: dict, initial_parameter: dict, history: List[dict]):
        try: 
            # input keys: text
            raise NotImplementedError
        
            # output keys: 'section'
        except Exception as e:
            raise Exception(f"execute :: {e}")
