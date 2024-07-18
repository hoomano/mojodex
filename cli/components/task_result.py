from textual.widgets import Markdown
from textual.containers import ScrollableContainer

class TaskResultDisplay(ScrollableContainer):

    def __init__(self, result: str, id: str) -> None:
        self.result = result
        super().__init__(id=id)
        self.styles.padding = 4

    def compose(self):
        yield Markdown(self.result)
