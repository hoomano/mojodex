import sys

sys.path.append("../")
from entities import MdUserTaskExecution

class UserTaskExecution(MdUserTaskExecution):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)