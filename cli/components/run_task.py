from textual.widget import Widget
from textual.widgets import Static
from textual.widgets import Button


class RunTaskLayout(Widget):

    def __init__(self, user_task_pk: int, id: str) -> None:
        self.user_task_pk = user_task_pk
        super().__init__(id=id)
        self.styles.padding = 4

    def compose(self):
        yield Static(str(self.user_task_pk))
        yield Button("🎙️")


    def on_button_pressed(self, event: Button.Pressed) -> None:
        pass