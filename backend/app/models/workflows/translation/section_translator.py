from models.workflows.step import WorkflowStep
from typing import List

class SectionsTranslatorStep(WorkflowStep):

    @property
    def description(self):
        return "Translate a section to the target language."

    @property
    def input_keys(self):
        return ['section']
    
    @property
    def output_keys(self):
        return ['translation']
    
    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict, history: List[dict]):
        # input keys: 'section'
        
        return [{'translation': parameter['section'] + ' in ' + initial_parameter['target_language']}]
    
        # output keys: 'translation'