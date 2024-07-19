from textual.widget import Widget
from entities.user_task_execution import NewUserTaskExecution
from services.user_services import create_user_task_execution
from components.chat import Chat


class RunTaskLayout(Widget):

    def __init__(self, user_task_pk: int) -> None:
        self.user_task_pk = user_task_pk
        self.user_task_execution : NewUserTaskExecution = create_user_task_execution(user_task_pk)
        super().__init__()
        self.init_message =f"{self.user_task_execution.json_input[0]['description_for_user']} \n{self.user_task_execution.json_input[0]['placeholder']}"
        self.chat = Chat(self.user_task_execution.session_id, self.init_message)
        # self.task_result_tab = Static("")
        # Messaging().on_draft_message_callback = on_new_result
        # def on_new_result(data):
        #   self.user_task_execution.new_result(data['produced_text_title'], data['produced_text_production'])
        #   self.task_result_tab.remove()
        #   self.task_result_tab = TaskResult(self.user_task_execution.concatenatedResult)
        #   self.task_result_tab.styles.width= '60%'
        #   self.app.call_from_thread(lambda: self.mount(self.task_result_tab, before=0))

    def compose(self):
        try:
            #yield Static("") # future TaskResult()
            yield self.chat
        except Exception as e:
            self.notify(message=f"Error: {e}", title="Error")


                    