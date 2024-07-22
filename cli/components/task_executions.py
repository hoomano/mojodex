import threading
from services.user_services import load_task_execution_list, load_task_execution_result
from components.task_result import TaskResultDisplay
from entities.user_task_execution import UserTaskExecutionListElementDisplay
from components.mojodex import Menu, MenuItem
from textual.widget import Widget
from textual.widgets import Static
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.keys import Keys

class TaskExecutionMenuItem(MenuItem):
    def __init__(self, user_task_execution: UserTaskExecutionListElementDisplay, action: callable, classes=None) -> None:
        self.user_task_execution_pk = user_task_execution.pk
        super().__init__(str(user_task_execution), action, id=f"user_task_execution_button_{user_task_execution.pk}", classes=classes)

class TaskExecutionsLayout(Widget):

    def constructTaskResultDisplay(self, user_task_execution_pk):
        return TaskResultDisplay(load_task_execution_result(user_task_execution_pk).concatenated_result, 
                                          id=f"user_task_execution_result_{user_task_execution_pk}")

    def __init__(self, id: str) -> None:
        
        self.user_task_executions: list[UserTaskExecutionListElementDisplay] = load_task_execution_list()
        self._initial_content = "task_list_execution_result"
        self.current_content =  self._initial_content
        self.menu = Menu(
        [
            TaskExecutionMenuItem(
                user_task_execution,
                lambda user_task_execution_pk: self.constructTaskResultDisplay(user_task_execution_pk),
            )
                
            for user_task_execution in self.user_task_executions
        ],
        id="task_list_execution_menu"
    )
        super().__init__(id=id)
        

    def compose(self) -> ComposeResult:
        with Vertical(id="task_list_execution_sidebar"):
            yield self.menu
        yield TaskResultDisplay("# Task Result\n# 😁\n Select the task from your history or create the first one.", id= self._initial_content)
        yield Static("") # Prepare future chat column


    def on_button_pressed(self, event: TaskExecutionMenuItem.Pressed) -> None:
        if isinstance(event.button, TaskExecutionMenuItem):
            menu_item = event.button
            if menu_item.id in [item.id for item in self.menu.menu_items]:
                
                body = self.query_one(f"#{self.current_content}", Widget)
                body.remove()
                
                task_mounting_thread = threading.Thread(target=self._mount_task, args=(menu_item,))
                task_mounting_thread.start()

    def _mount_task(self, menu_item):
        widget = menu_item.action(menu_item.user_task_execution_pk)
        self.current_content = widget.id
        self.app.call_from_thread(lambda: self.mount(widget))
