from abc import ABC, abstractmethod

class Parameter:
    def __init__(self, dict_of_values):
        self.value = dict_of_values


class StepInput(ABC):
    @abstractmethod
    def __init__(self, input):
        pass

class OneParamStepInput(StepInput):
    # input is a param
    def __init__(self, value: Parameter):
        self.value = value
    

class MultiParamStepInput(StepInput):
    # input is a list of params
    def __init__(self, value: list[Parameter]):
        self.value = value


class Step(ABC):
    def __init__(self, input):
        print("Step __init__")

class SimpleStep(Step):
    def __init__(self, input: OneParamStepInput):
        print("SimpleStep __init__")

class MultiStep(Step):
    def __init__(self, input: MultiParamStepInput):
        print("MultiStep __init__")


    