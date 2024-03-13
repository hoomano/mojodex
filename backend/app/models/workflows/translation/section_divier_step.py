class SectionsDividerStep:
    
    def execute(self, parameter, initial_parameters, history):
        return parameter.split("\n")
    

    def concatenate_runs_results(self, runs_results):
        results = []
        for run in runs_results:
            if run:
                results += run
        return results
