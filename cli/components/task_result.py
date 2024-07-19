from textual.widgets import Markdown
from textual.containers import ScrollableContainer

class TaskResultDisplay(ScrollableContainer):

    def __init__(self, result: str, id: str) -> None:
        try:
            self.result = result
            
            super().__init__(id=id)
            self.styles.padding = 4
            self.styles.border = ("round", "green")
        except Exception as e:
            self.notify(f"Error creating TaskResultDisplay: {e}")

   
        
    def compose(self):
        yield Markdown(self.result)
