from datetime import datetime
from textual.widget import Widget
from textual.widgets import Static
from textual.widgets import Button, Markdown
from textual.containers import Vertical, Container
import threading
from textual.app import ComposeResult
from entities.session import Session
from services.messaging import Messaging
from services.audio import AudioRecorder
from services.user_services import start_user_task_execution
from entities.message import Message


class MicButton(Button):
    def __init__(self, id: str):
        self.is_recording = False
        super().__init__("🎤", id=id)
        self.styles.width='100%'
        self.styles.margin = 1
    
    def switch(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.variant='error'
            self.label='🔴'
        else:
            self.variant='success'
            self.label = '🎤'
        
    
class MessageWidget(Static):
    def __init__(self, message: Message) -> None:
        self.message = message
        super().__init__(f"{self.message.icon}:  {self.message.message}")
        self.styles.border = ("round", "lightgrey") if self.message.author == "mojo" else ("round", "dodgerblue")
        self.styles.color = "lightgrey" if self.message.author == "mojo" else "dodgerblue"   



class MessagesList(Static):
    def __init__(self, messages: list[Message]) -> None:
        try:
            self.messages = messages
            super().__init__(classes="chat-messages-panel")
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error")

    def compose(self) -> ComposeResult:
        try:
            for message in self.messages:
                yield MessageWidget(message)
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error")

class Chat(Widget):

    def __init__(self, session_id: str, init_message:str) -> None:
        self.session = Session(session_id)
        self.mic_button_id = 'mic_button'
        self.recorder = AudioRecorder()
        self.recording_thread = None
        self.init_message = init_message

        Messaging().connect_to_session(self.session.session_id)
        Messaging().on_mojo_message_callback = self.on_mojo_message_callback
        
        super().__init__()

        self.styles.height = "100%"
        self.styles.content_align = ("center", "bottom")

        self.mic_button_widget = MicButton(id=self.mic_button_id)
       
        self.messages_list_widget =  MessagesList(self.session.messages) if self.session.messages else Markdown(self.init_message, id="task_execution_description")

    def on_mojo_message_callback(self, message_from_mojo):
        try:
            message = Message(message_from_mojo["message_pk"], message_from_mojo['text'], "mojo")
            self.session.messages.append(message)
            self.messages_list_widget.remove()
            mounting_on = self.query_one(f"#chat-interface", Widget)
            self.messages_list_widget = MessagesList(self.session.messages)
            self.app.call_from_thread(lambda: mounting_on.mount(self.messages_list_widget, before=0))
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error")

    def compose(self):
        try:
            with Vertical(id="chat-interface"):
                yield self.messages_list_widget
                yield self.mic_button_widget        
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error")


    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id.startswith(self.mic_button_id) and isinstance(event.button, MicButton):
            button = event.button
            if not button.is_recording:
                if self.recording_thread is None or not self.recording_thread.is_alive():
                    self.recording_thread = threading.Thread(target=self.recorder.start_recording, args=(self.notify,))
                    self.recording_thread.start()

            else:
                if self.recording_thread and self.recording_thread.is_alive():
                    self.recorder.stop_recording(self.notify)
                    self.recording_thread.join()                    

                    message : Message = start_user_task_execution(self.session.session_id, datetime.now().isoformat())
                    self.session.messages.append(message)

                    self.messages_list_widget.remove()
                    mounting_on = self.query_one(f"#chat-interface", Widget)
                    self.messages_list_widget = MessagesList(self.session.messages)
                    mounting_on.mount(self.messages_list_widget, before=0)
      

            button.switch()
                    
                    