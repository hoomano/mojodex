class SectionsTranslatorStep:
    
    def execute(self, parameter, initial_parameters, history):
        return parameter + ' in ' + initial_parameters['target']
    

    def concatenate_runs_results(self, runs_results):
        return ' '.join([run.result for run in runs_results])