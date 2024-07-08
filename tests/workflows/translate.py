from workflow import Step, Workflow, Run

class SectionDividerStep(Step):
    def _execute(self, parameter, initial_parameters, history):
        return parameter['text'].split(', ')
    
    def _concatenate_runs_results(self):
        # each run.result of runs is a list, I want to concatenate them
        results = []
        for run in self.runs:
            if run.result:
                results += run.result
        return results
    
class SectionTranslationStep(Step):
    def _execute(self, parameter, initial_parameters, history):
        return parameter + ' in ' + initial_parameters['target']
    
    def _concatenate_runs_results(self):
        # each run.result of runs is a string, I want to concatenate them
        return ' '.join([run.result for run in self.runs])

section_division = SectionDividerStep('section_division', checkpoint=True)
section_translation = SectionTranslationStep('section_translation', checkpoint=True)


translate = Workflow('translate', [section_division, section_translation], initial_parameters={'target': 'en', 'text': 'Salut, comment ça va?'})

translate.run()