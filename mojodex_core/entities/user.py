import sys

sys.path.append("../")
from entities import MdUser


class User(MdUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_greeting(self):
        return f"Hello, {self.name}!"

