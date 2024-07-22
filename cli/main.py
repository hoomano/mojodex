from services.messaging import Messaging
from components.new_task import NewTaskLayout
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
                MenuItem("✚ New Task", lambda: NewTaskLayout(id="body_new_task"), id="new_task"),
                MenuItem("📋 Tasks", lambda: TaskExecutionsLayout(id="body_task_executions"), id="task_list"),
                MenuItem("☛ Logout", lambda: Static("Logout", id="body_logout"), id="logout")
            ], id='main_menu')

    app = Mojodex(main_menu)
    Messaging().notify = app.notify
    Messaging().start()

    app.run()

