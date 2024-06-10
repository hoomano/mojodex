import sys

sys.path.append("../")
from entities import MdUserTask

class UserTask(MdUserTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)