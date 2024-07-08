from abc import ABC, abstractmethod

class Workflow:
    def __init__(self, name, steps, initial_parameters):
        self.name = name
        self.steps = steps
        self.initial_parameters = initial_parameters

    def run(self):
        step_to_run = self._current_step
        print(f"🟢 Running step: {step_to_run.name} - parameters: {self.intermediate_results[-1] if self.intermediate_results else [self.initial_parameters]} ")
        step_to_run.initialize_runs(self.intermediate_results[-1] if self.intermediate_results else [self.initial_parameters])
        result = step_to_run.run(self.initial_parameters, self.intermediate_results)
        validation = self._ask_for_validation(result)
        if validation:
            self.validate()
        else:
            self.invalidate()
        self.run()

    @property
    def _current_step(self):
        # step to run is:
        # last one initialized which runs are not all validated
        # or first step not initialized
        # browse steps backwards
        for step in reversed(self.steps):
            if step.initialized and not step.validated:
                return step
        # else, next step to run is the first one not initialized
        for step in self.steps:
            if not step.initialized:
                return step
        return None
        
    @property
    def intermediate_results(self):
        return [step.result for step in self.steps[:-1] if step.initialized]

    def _ask_for_validation(self, result):
        print(f"---- ASK FOR VALIDATION ----\n{result}\n ------ END -----")
        user_validation = input("Is this result valid? (y/n): ")
        return user_validation == 'y'


    def validate(self):
        self._current_step.current_run.validate()

    def _find_checkpoint_step(self):
        for step in reversed(self.steps):
            if step.initialized and step.checkpoint:
                return step
        return None

    def invalidate(self):
        # find checkpoint step
        checkpoint_step = self._find_checkpoint_step()
        # if there are other steps after checkpoint, reset them
        if not checkpoint_step:
            for step in self.steps:
                step.reset()
        else:
            # reset steps after checkpoint
            checkpoint_step_index = self.steps.index(checkpoint_step)
            for step in self.steps[checkpoint_step_index+1:]:
                step.reset()
        

class Step(ABC):
    def __init__(self, name, checkpoint=False):
        self.name = name
        self.checkpoint = checkpoint
        self.runs = []
        self.initialized = False

    def initialize_runs(self, parameters):
        if not self.initialized:
            self.runs = [Run(parameter) for parameter in parameters]
            self.initialized = True

    def reset(self):
        self.runs = []
        self.initialized = False
            
    @property
    def validated(self):
        return all(run.validated for run in self.runs)

    def run(self, initial_parameters, history):
        # run from non-validated actions
        for run in self.runs:
            print(f"👉 Step {self.name} :: run {run.parameter}")
            if not run.validated:
                return self.execute(run, initial_parameters, history)
            
    @abstractmethod
    def _execute(self, parameter, initial_parameters, history):
        pass

    def execute(self, run, initial_parameters, history):
        result = self._execute(run.parameter, initial_parameters, history)
        run.executed = True
        run.result = result
        return run.result

    @property
    def result(self):
        return self._concatenate_runs_results()
    
    @abstractmethod
    def _concatenate_runs_results(self):
        pass
    
    @property
    def current_run(self):
        for run in self.runs:
            if not run.validated:
                return run

class Run(ABC):

    def __init__(self, parameter):
        self.validated = False
        self.executed = False
        self.parameter = parameter
        self.result = None

    def validate(self):
        self.validated = True