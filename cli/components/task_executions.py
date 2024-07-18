from entities.user_task_execution import UserTaskExecutionListElementDisplay
from components.mojodex import Menu, MenuItem
from textual.widget import Widget
from textual.widgets import Static
from textual.app import ComposeResult
from textual.containers import Vertical
from entities.user import User
from textual.widgets import Markdown
from textual.containers import ScrollableContainer



class TaskExecutionsLayout(Widget):
    def __init__(self, user: User, id: str) -> None:
        
        self.user_task_executions: list[UserTaskExecutionListElementDisplay] = user.load_task_execution_list()
        self._initial_content = "task_list_execution_result"
        self.current_content =  self._initial_content
        self.menu = Menu(
        [
            MenuItem(
                str(user_task_execution), 
                Markdown(user.load_task_execution_result(user_task_execution.pk).concatenated_result, id=f"user_task_execution_result_{user_task_execution.pk}"), 
                id=f"user_task_execution_button_{user_task_execution.pk}") 
            for user_task_execution in self.user_task_executions
        ],
        id="task_list_execution_menu"
    )
        super().__init__(id=id)
        

    def compose(self) -> ComposeResult:
        with Vertical(id="task_list_execution_sidebar"):
            yield self.menu
        yield Markdown("#Task Result", id= self._initial_content)
        yield Static("") # Prepare future chat column


    def on_button_pressed(self, event: MenuItem.Pressed) -> None:
        if isinstance(event.button, MenuItem):
            widget = event.button.widget
            if widget.id in [item.widget.id for item in self.menu.menu_items]:
                body = self.query_one(f"#{self.current_content}", Widget)
                body.remove()
                self.current_content = widget.id
                widget.styles.padding = 4
                self.mount(widget)
