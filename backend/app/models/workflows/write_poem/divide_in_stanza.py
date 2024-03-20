from models.workflows.step import WorkflowStep
import json
from typing import List
        

class StanzaDividerStep(WorkflowStep):

    @property
    def description(self):
        return "Determine theme of each stanza."

    def __init__(self, workflow_step):
        super().__init__(workflow_step, input_keys=['theme', 'n_stanza'], output_keys=['stanza_theme'])

    
    def _execute(self, parameter: dict, initial_parameter: dict, history: List[dict]):
        try: 
            # input keys: theme, n_stanza
            raise NotImplementedError
        
            # output keys: 'stanza_theme'
        except Exception as e:
            raise Exception(f"execute :: {e}")
