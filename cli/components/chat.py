from datetime import datetime
from textual.widget import Widget, events
from textual.widgets import Static
from textual.widgets import Button, Markdown, LoadingIndicator
from textual.containers import Vertical
from textual.app import ComposeResult
from textual import work
import threading
from entities.session import Session
from services.messaging import Messaging
from services.audio import AudioRecorder
from services.user_services import start_user_task_execution
from entities.message import PartialMessage, Message
import time


class MicButton(Button):
    def __init__(self, id: str):
        self.is_recording = False
        super().__init__("🎤", id=id)
        self.styles.width='100%'

    
    def switch(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.variant='error'
            self.label='🔴'
            self.active_effect_duration = 0
        else:
            self.variant='success'
            self.label = '🎤'
            self.active_effect_duration = 0.2


    
class MessageWidget(Static):
    def __init__(self, message: PartialMessage) -> None:
        self.message = message
        super().__init__(f"{self.message.icon}:  {self.message.message}")
        self.styles.border = ("round", "lightgrey") if self.message.author == "mojo" else ("round", "dodgerblue")
        self.styles.color = "lightgrey" if self.message.author == "mojo" else "dodgerblue"   

class MessagesList(Static):
    def __init__(self, messages: list[PartialMessage], session_id: str) -> None:
        try:
            self.messages = messages
            self.partial_message_placeholder : PartialMessage = None
            self.session_id = session_id 
            self.message_placeholder_widget = None
            if self.messages[-1].author == "user":
                self.partial_message_placeholder = PartialMessage("", "mojo")
                self.message_placeholder_widget = MessageWidget(self.partial_message_placeholder)
                Messaging().on_mojo_token_callback = self.on_mojo_token_callback
            super().__init__(classes="chat-messages-panel")
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error")

    def on_mojo_token_callback(self, token_from_mojo):
        try:
            if self.message_placeholder_widget:
                self.partial_message_placeholder.message=token_from_mojo['text']
                self.message_placeholder_widget.update(f"{self.partial_message_placeholder.icon}:  {self.partial_message_placeholder.message}")
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error")


    def compose(self) -> ComposeResult:
        try:
            for message in self.messages:
                if not message.is_draft:
                    yield MessageWidget(message)
            if self.message_placeholder_widget:
                yield self.message_placeholder_widget
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error")

class Chat(Widget):

    def __init__(self, session_id: str, init_message:str, on_new_result: callable) -> None:
        self.session = Session(session_id)
        self.mic_button_id = 'mic_button'
        self.mic_button_height = 8
        self.mic_button_margin = 1
        self.recorder = AudioRecorder()
        self.recording_thread = None
        self.init_message = init_message
        self.partial_message_placeholder : PartialMessage = None

        self.on_new_result = on_new_result
        Messaging().connect_to_session(self.session.session_id)
        Messaging().on_mojo_message_callback = self.on_mojo_message_callback
        Messaging().on_draft_message_callback = self.on_draft_message_callback
        
        super().__init__()

        self.styles.height = "100%"
        self.styles.content_align = ("center", "bottom")

        self.mic_button_widget = MicButton(id=self.mic_button_id)
        self.mic_button_widget.styles.height=self.mic_button_height
        self.mic_button_widget.styles.margin = self.mic_button_margin
       
        self.messages_list_widget =  MessagesList(self.session.messages, self.session.session_id) if self.session.messages else Markdown(self.init_message, id="task_execution_description")
        self.loading_indicator = LoadingIndicator()
        self.loading_indicator.styles.height=self.mic_button_height
        self.loading_indicator.styles.margin = self.mic_button_margin

    def on_draft_message_callback(self, message_from_mojo):
        try:
            self.on_new_result(message_from_mojo)
            message = Message(message_from_mojo["message_pk"], message_from_mojo['text'], "mojo", is_draft=True)
            self.session.messages.append(message)

            self._update_chat_interface_on_message_receveived()
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error")

    def on_mojo_message_callback(self, message_from_mojo):
        try:
            message = Message(message_from_mojo["message_pk"], message_from_mojo['text'], "mojo")
            self.session.messages.append(message)

            self._update_chat_interface_on_message_receveived()
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error")


    def _update_chat_interface_on_message_receveived(self):
        try:
            self.messages_list_widget.remove()
            mounting_on = self.query_one(f"#chat-interface", Widget)
            self.messages_list_widget = MessagesList(self.session.messages, self.session.session_id)
            self.app.call_from_thread(lambda: mounting_on.mount(self.messages_list_widget, before=0))

            self.loading_indicator.remove()
            mounting_on = self.query_one(f"#chat-interface", Widget)
            self.app.call_from_thread(lambda: mounting_on.mount(self.mic_button_widget))
        except Exception as e:
            raise Exception(f"_update_chat_interface_on_message_receveived: {e}")

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
                    self.mic_button_widget.remove()
                    mounting_on = self.query_one(f"#chat-interface", Widget)
                    mounting_on.mount(self.loading_indicator)
                    thread = threading.Thread(target=self.process_recording)
                    thread.start()
            button.switch()

              
                    
    def process_recording(self):
                    
        self.recorder.stop_recording(self.notify)
        self.recording_thread.join()   

        message : Message = start_user_task_execution(self.session.session_id, datetime.now().isoformat())
        self.session.messages.append(message)

        self.messages_list_widget.remove()
        mounting_on = self.query_one(f"#chat-interface", Widget)
        self.messages_list_widget = MessagesList(self.session.messages, self.session.session_id)
        self.app.call_from_thread(lambda: mounting_on.mount(self.messages_list_widget, before=0))

        
       
    
    
                    