from models.workflows.step import WorkflowStep, WorkflowStepDataSpec
import json
        
        

class SectionsDividerStep(WorkflowStep):

    def __init__(self, workflow_step):
        super().__init__(workflow_step)

    
    def _execute(self, parameter: dict, initial_parameter: dict, history: list[dict]):
        try: 
            # input keys: text
            
            # decode parameter from string to json
            print(f"👉 parameter: {parameter}")
            parameter = json.loads(parameter)
            sections=parameter['text'].split("\n")
            return [{'section': section} for section in sections]
        
            # output keys: 'section'
        except Exception as e:
            raise Exception(f"execute :: {e}")
