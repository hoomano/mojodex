from datetime import datetime
from textual.widget import Widget
from textual.widgets import Static
from textual.widgets import Button
from textual.containers import Vertical
import threading
from textual.app import ComposeResult

from services.audio import AudioRecorder
from entities.user_task_execution import NewUserTaskExecution
from services.user_services import create_user_task_execution, start_user_task_execution
from entities.message import Message


class MessageWidget(Static):
    def __init__(self, message: Message, id: str) -> None:
        self.message = message
        super().__init__(f"{self.message.icon}:  {self.message.message}", id=id)



class InteractionHistory(Static):
    def __init__(self, init_message, messages: list[Message], id: str) -> None:
        try:
            self.init_message = init_message
            self.messages = messages
            super().__init__(id=id)
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error")

    def compose(self) -> ComposeResult:
        try:
            self.notify(f"Len messages: {len(self.messages)}", title = "InteractionHistory")
            if not self.messages:
                yield Static(self.init_message, id="task_execution_description")
            for message in self.messages:
                self.notify(f"yielding message {message.pk}", title="InteractionHistory")
                yield MessageWidget(message, id = f"message_pk_{message.pk}")
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error")

class RunTaskLayout(Widget):

    def __init__(self, user_task_pk: int, id: str) -> None:
        self.user_task_pk = user_task_pk
        self.mic_button_id = 'mic_button'
        self.recorder = AudioRecorder()
        self.recording_thread = None

        self.user_task_execution : NewUserTaskExecution = create_user_task_execution(user_task_pk)
        
        super().__init__(id=id)
        self.styles.padding = 4

        self.start_button = Button("🎙️", id=self.mic_button_id+"_start", variant="success")
        self.stop_button =  Button("🔴", id=self.mic_button_id+"_stop", variant="error")
        init_message =f"{self.user_task_execution.json_input[0]['description_for_user']} \n{self.user_task_execution.json_input[0]['placeholder']}"

        self.interaction_history = InteractionHistory(init_message, 
                                     self.user_task_execution.messages, id="interaction_history")
        self.notify(self.interaction_history.init_message, title="Task")

    def compose(self):
        try:
            with Vertical(id="task_execution_panel"):

                yield self.interaction_history
                yield self.start_button
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error")
            
        

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id.startswith(self.mic_button_id):
            button_id = event.button.id
            if button_id.endswith("start"):
                self.notify(message="start", title="Record")
                if self.recording_thread is None or not self.recording_thread.is_alive():
                    self.notify(message="starting thread", title="Record")
                    self.recording_thread = threading.Thread(target=self.recorder.start_recording, args=(self.notify,))
                    self.recording_thread.start()


                    self.start_button.remove()
                    mounting_on = self.query_one(f"#task_execution_panel", Widget)
                    mounting_on.mount(self.stop_button)

            elif button_id.endswith("stop"):
                self.notify(message="stop", title="Record")
                if self.recording_thread and self.recording_thread.is_alive():
                    self.notify(message="stopping thread", title="Record")
                    self.recorder.stop_recording(self.notify)
                    self.recording_thread.join()

                    self.stop_button.remove()
                    
                    # call route
                    message : Message = start_user_task_execution(self.user_task_execution.session_id, datetime.now().isoformat())
                    self.notify(f"pk: {message.pk} - {message.message}", title='Message')
                    self.user_task_execution.messages.append(message)

                    self.interaction_history.remove()
                    mounting_on = self.query_one(f"#task_execution_panel", Widget)
                    self.interaction_history = InteractionHistory(f"{self.user_task_execution.json_input[0]['description_for_user']} \n{self.user_task_execution.json_input[0]['placeholder']}", 
                                     self.user_task_execution.messages, id=f"interaction_history_{len(self.user_task_execution.messages)}")
                    mounting_on.mount(self.interaction_history)
                    mounting_on.mount(self.start_button)
                    
                    