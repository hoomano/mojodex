from views.mojodex import Menu, Mojodex, MenuItem
from services.auth import login

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
                MenuItem("New Task", lambda: "New Task"),
                MenuItem("List Tasks", user.task_execution_list_as_str),
                MenuItem("Logout", lambda: "Logout")
            ])

    app = Mojodex(main_menu)

    app.run()
