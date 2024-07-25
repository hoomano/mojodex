import threading
from services.user_services import load_task_execution_list, load_task_execution_result
from components.task_result import TaskResultDisplay
from entities.user_task_execution import UserTaskExecutionListElementDisplay
from components.mojodex import Menu, MenuItem
from textual.widget import Widget
from textual.widgets import Static
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.binding import Binding
import pyperclip

class TaskExecutionMenuItem(MenuItem):
    def __init__(self, user_task_execution: UserTaskExecutionListElementDisplay, classes=None) -> None:
        self.user_task_execution_pk = user_task_execution.pk
        super().__init__(str(user_task_execution), action=None, id=f"user_task_execution_button_{user_task_execution.pk}", classes=classes)

class TaskExecutionsLayout(Widget):

    def constructTaskResultDisplay(self, user_task_execution_pk):
        return load_task_execution_result(user_task_execution_pk).concatenated_result

    def __init__(self, id: str) -> None:
        
        self.user_task_executions: list[UserTaskExecutionListElementDisplay] = load_task_execution_list()
        self.result_widget = TaskResultDisplay("# Task Result\n# 😁\n Select the task from your history or create the first one.")
        self.result = None
        self.menu = Menu(
        [
            TaskExecutionMenuItem(
                user_task_execution,
            )
                
            for user_task_execution in self.user_task_executions
        ]
    )
        self.menu.styles.margin = (0,0,0,1)
        super().__init__(id=id)
        
   
    BINDINGS = [
        Binding(key="c", action="copy", description="Copy"),
    ]

    def action_copy(self):
        try:
            pyperclip.copy(self.result)
            self.notify(f"Copied to clipboard")
        except Exception as e:
            self.notify(f"Error copying to clipboard: {e}", level="error", title="Error")

    def compose(self) -> ComposeResult:
        with Vertical(id="task_list_execution_sidebar"):
            yield self.menu
        yield self.result_widget
        yield Static("") # Prepare future chat column


    def on_button_pressed(self, event: TaskExecutionMenuItem.Pressed) -> None:
        if isinstance(event.button, TaskExecutionMenuItem):
            menu_item = event.button
            if menu_item.id in [item.id for item in self.menu.menu_items]:
                self.result = load_task_execution_result(menu_item.user_task_execution_pk).concatenated_result
                self.result_widget.update(self.result)

