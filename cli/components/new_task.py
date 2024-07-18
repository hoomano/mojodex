from textual.widget import Widget
from components.menu import Menu, MenuItem
from entities.user import User
from entities.user_task import UserTaskListElementDisplay
from textual.widgets import Static
from textual.app import ComposeResult
class NewTaskLayout(Widget):

    def __init__(self, user: User, id: str) -> None:
        
        self.user_tasks: list[UserTaskListElementDisplay] = user.load_user_tasks_list()
        self.grid_task_id = "grid-task"
        self.menu = Menu(
        [
            MenuItem(
                str(user_task), 
                Static("", id=f"user_task_clicked_{user_task.pk}"), 
                id=f"user_task_button_{user_task.pk}")
            for user_task in self.user_tasks
        ],
        id=self.grid_task_id
    )
        for menu_item in self.menu.menu_items:
            menu_item.styles.height='100%'
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        yield self.menu



    def on_button_pressed(self, event: MenuItem.Pressed) -> None:
        if isinstance(event.button, MenuItem):
            widget = event.button.widget
            if widget.id in [item.widget.id for item in self.menu.menu_items]:
                self.notify(f"Clicked on #{widget.id}")
                body = self.query_one(f"#{self.grid_task_id}", Widget)
                body.remove()
                self.mount(widget)
