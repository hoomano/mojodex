from entities.user_task_execution import UserTaskExecutionListElementDisplay
from views.mojodex import Menu, Mojodex, MenuItem
from services.auth import login
from textual.widgets import Static

import logging
from rich.traceback import install
from rich.logging import RichHandler


logging.basicConfig(
    level="ERROR",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

# Install Rich traceback globally to handle exceptions beautifully
install()

user = None

def task_list_button():
    user_task_executions: list[UserTaskExecutionListElementDisplay] = user.load_task_execution_list()
    return Menu(
            [
                MenuItem(
                    str(user_task_execution), 
                    lambda: str(user_task_execution), 
                    id=f"user_task_execution_{user_task_execution.pk}") 
                for user_task_execution in user_task_executions
            ],
            id="body_task_list"
            )

if __name__ == "__main__":
    user = login()

    main_menu = Menu([
                MenuItem("New Task", lambda: Static("New Task", id="body_new_task")),
                MenuItem("List Tasks", task_list_button),
                MenuItem("Logout", lambda: Static("Logout", id="body_logout"))
            ], id='main_menu')

    app = Mojodex(main_menu)

    app.run()

