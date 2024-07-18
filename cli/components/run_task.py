from textual.widget import Widget
from textual.widgets import Static
from textual.widgets import Button
from textual.containers import Vertical
import threading


from services.audio import AudioRecorder
from entities.user_task_execution import NewUserTaskExecution
from services.user_services import create_user_task_execution


class RunTaskLayout(Widget):

    def __init__(self, user_task_pk: int, id: str) -> None:
        self.user_task_pk = user_task_pk
        self.mic_button_id = 'mic_button'
        self.recorder = AudioRecorder()
        self.recording_thread = None

        self.user_task_execution : NewUserTaskExecution = create_user_task_execution(user_task_pk)
        
        super().__init__(id=id)
        self.styles.padding = 4

    def compose(self):
        with Vertical(id="task_execution_panel"):
            yield Static(f"{self.user_task_execution.json_input[0]['description_for_user']} \n{self.user_task_execution.json_input[0]['placeholder']}", id="task_execution_description")
            yield Button("🎙️", id=self.mic_button_id+"_start", variant="success")
            yield Button("🔴", id=self.mic_button_id+"_stop", variant="error")
            
        

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id.startswith(self.mic_button_id):
            button_id = event.button.id
            if button_id.endswith("start"):
                self.notify(message="start", title="Record")
                if self.recording_thread is None or not self.recording_thread.is_alive():
                    self.notify(message="starting thread", title="Record")
                    self.recording_thread = threading.Thread(target=self.recorder.start_recording, args=(self.notify,))
                    self.recording_thread.start()
            elif button_id.endswith("stop"):
                self.notify(message="stop", title="Record")
                if self.recording_thread and self.recording_thread.is_alive():
                    self.notify(message="stopping thread", title="Record")
                    self.recorder.stop_recording(self.notify)
                    self.recording_thread.join()