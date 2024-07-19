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
        self.chat = Chat(self.user_task_execution.session_id, self.init_message)
        self.chat.styles.width = "100%"
        self.task_result_panel= None

        Messaging().on_draft_message_callback = self.on_new_result

    def on_new_result(self, data):
        try:
            self.user_task_execution.new_result(data['produced_text_title'], data['produced_text'])
            produced_text_version_pk = data['produced_text_version_pk']
            if self.task_result_panel:
                self.task_result_panel.remove()
            self.task_result_panel = TaskResultDisplay(self.user_task_execution.concatenated_result, id=f"user_task_execution_produced_text_version_{produced_text_version_pk}")
            self.task_result_panel.styles.width = "60%"
            self.chat.styles.width = "40%"
            mounting_on = self.query_one(f"#horizontal-task-execution-panel", Widget)
            self.app.call_from_thread(lambda: mounting_on.mount(self.task_result_panel, before=0))
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


                    