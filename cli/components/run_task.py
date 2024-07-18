from textual.widget import Widget
from textual.widgets import Static
from textual.widgets import Button
from textual.containers import Vertical, Container

from entities.user_task_execution import NewUserTaskExecution
from services.user_services import create_user_task_execution


class RunTaskLayout(Widget):

    def __init__(self, user_task_pk: int, id: str) -> None:
        self.user_task_pk = user_task_pk
        self.mic_button_id = 'mic_button'
        self.user_task_execution : NewUserTaskExecution = create_user_task_execution(user_task_pk)
        
        super().__init__(id=id)
        self.styles.padding = 4

    def compose(self):
        with Vertical(id="task_execution_panel"):
            yield Static(f"{self.user_task_execution.json_input[0]['description_for_user']} \n{self.user_task_execution.json_input[0]['placeholder']}", id="task_execution_description")
            yield Button("🎙️", id=self.mic_button_id)
            
        


    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == self.mic_button_id:
            pass