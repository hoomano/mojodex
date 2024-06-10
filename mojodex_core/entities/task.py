import sys
sys.path.append("../")
from entities import MdTask
from jinja2 import Template
class Task(MdTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InstructTask(Task):

    @property
    def instructions(self):
        try:
            print("instructions")
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: instructions :: {e}")


class Workflow(Task):

    @property
    def steps(self):
        try:
            print("steps")
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: steps :: {e}")