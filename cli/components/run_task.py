from textual.widget import Widget
from entities.user_task_execution import NewUserTaskExecution
from services.user_services import create_user_task_execution
from components.chat import Chat
from components.task_result import TaskResultDisplay
from textual.containers import Horizontal
from services.messaging import Messaging

class RunTaskLayout(Widget):

    def __init__(self, user_task_pk: int) -> None:
        self.user_task_pk = user_task_pk
        self.user_task_execution : NewUserTaskExecution = create_user_task_execution(user_task_pk)
        super().__init__()
        self.init_message =f"{self.user_task_execution.json_input[0]['description_for_user']} \n{self.user_task_execution.json_input[0]['placeholder']}"
        self.chat = Chat(self.user_task_execution.session_id, self.init_message, self.on_new_result)
        self.chat.styles.width = "100%"
        self.task_result_panel= None


        Messaging().on_draft_token_callback = self.on_result_token

    def on_new_result(self, message_from_mojo):
        try:
            if message_from_mojo["session_id"] != self.user_task_execution.session_id:
                return
            self.user_task_execution.new_result(message_from_mojo['produced_text_title'], message_from_mojo['produced_text'])
            self.app.call_from_thread(lambda: self.task_result_panel.update(self.user_task_execution.concatenated_result))
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error", severity="error", timeout=20)

    def on_result_token(self, token_from_mojo):
        try:
            if token_from_mojo["session_id"] != self.user_task_execution.session_id:
                return
            new_text =f"{token_from_mojo['produced_text_title']}\n{token_from_mojo['produced_text']}"
            if not self.task_result_panel:
                self.task_result_panel = TaskResultDisplay(new_text)
                self.task_result_panel.styles.width = "60%"
                self.chat.styles.width = "40%"
                mounting_on = self.query_one(f"#horizontal-task-execution-panel", Widget)
                self.app.call_from_thread(lambda: mounting_on.mount(self.task_result_panel, before=0))
            else:
                self.app.call_from_thread(lambda: self.task_result_panel.update(new_text))
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error", severity="error", timeout=20)

    def compose(self):
        try:
            with Horizontal(id='horizontal-task-execution-panel', classes="task-execution-panel"):
                if self.task_result_panel:
                    yield self.task_result_panel
                yield self.chat
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error", severity="error")


                    