from models.workflows.step import WorkflowStep
import json
from typing import List
import time

class SectionsDividerStep(WorkflowStep):


    @property
    def description(self):
        return "Divide a text into sections."

    @property
    def input_keys(self):
        return ['text']
    
    @property
    def output_keys(self):
        return ['section']

    
    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict, history: List[dict]):
        try: 
            # input keys: text
            time.sleep(2)
            sections=parameter['text'].split("\n")
            return [{'section': section} for section in sections]
        
            # output keys: 'section'
        except Exception as e:
            raise Exception(f"execute :: {e}")
