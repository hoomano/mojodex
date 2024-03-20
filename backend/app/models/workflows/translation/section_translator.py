from models.workflows.step import WorkflowStep
from typing import List

class SectionsTranslatorStep(WorkflowStep):

    @property
    def description(self):
        return "Translate a section to the target language."

    def __init__(self, workflow_step):
        super().__init__(workflow_step, input_keys=['section'], output_keys=['translation'])
    
    def _execute(self, parameter: dict, initial_parameter: dict, history: List[dict]):
        # input keys: 'section'
        
        return [{'translation': parameter['section'] + ' in ' + initial_parameter['target_language']}]
    
        # output keys: 'translation'