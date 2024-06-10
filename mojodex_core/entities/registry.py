# registry.py
import sys

sys.path.append("../")
from entities import *

class ModelRegistry:
    registry = {}

    @classmethod
    def register(cls, name, model):
        cls.registry[name] = model

    @classmethod
    def get(cls, name):
        return cls.registry.get(name)

from user import User
from task import Task
ModelRegistry.register('MdUser', User)
ModelRegistry.register('MdTask', Task)
