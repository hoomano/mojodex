from components.task_executions import TaskExecutionsLayout
from components.mojodex import Menu, Mojodex, MenuItem
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

if __name__ == "__main__":
    user = login()

    main_menu = Menu([
                MenuItem("New Task", Static("New Task", id="body_new_task")),
                MenuItem("List Tasks", TaskExecutionsLayout(user, id="body_task_executions")),
                MenuItem("Logout", Static("Logout", id="body_logout"))
            ], id='main_menu')

    app = Mojodex(main_menu)

    app.run()
