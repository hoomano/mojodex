from textual.widget import Widget
from services.user_services import load_user_tasks_list
from components.run_task import RunTaskLayout
from components.menu import Menu, MenuItem
from entities.user import User
from entities.user_task import UserTaskListElementDisplay
from textual.app import ComposeResult

class NewTaskMenuItem(MenuItem):
    def __init__(self, user_task: UserTaskListElementDisplay, action: callable, classes=None) -> None:
        self.user_task_pk = user_task.pk
        super().__init__(str(user_task), action, id=f"user_task_button_{user_task.pk}", classes=classes)

class NewTaskLayout(Widget):

    def __init__(self, id: str) -> None:
        
        self.user_tasks: list[UserTaskListElementDisplay] = load_user_tasks_list()
        self.grid_task_id = "grid-task"
        self.menu = Menu(
        [
            NewTaskMenuItem(
                user_task, 
                lambda user_task_pk: RunTaskLayout(user_task_pk)
                )
            for user_task in self.user_tasks
        ],
        id=self.grid_task_id
    )
        for menu_item in self.menu.menu_items:
            menu_item.styles.height="100%"
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        yield self.menu



    def on_button_pressed(self, event: NewTaskMenuItem.Pressed) -> None:
        if isinstance(event.button, NewTaskMenuItem):
            menu_item = event.button
            if menu_item.id in [item.id for item in self.menu.menu_items]:
                body = self.query_one(f"#{self.grid_task_id}", Widget)
                body.remove()
                widget = menu_item.action(menu_item.user_task_pk)
                self.mount(widget)
