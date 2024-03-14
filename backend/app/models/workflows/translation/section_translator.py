from models.workflows.step import WorkflowStep

class SectionsTranslatorStep(WorkflowStep):
    
    def execute(self, parameter: dict, initial_parameter: dict, history: list[dict]):
        # input keys: 'section'

        return [{'translation': parameter + ' in ' + initial_parameter['target']}]
    
        # output keys: 'translation'