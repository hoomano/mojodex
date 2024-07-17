from rich.console import Console
from views.menu import Menu, MenuItem
from services.auth import login

def main():
    console = Console()
    # user login
    user = login()

    menu_items = [
        MenuItem("New Task", lambda: print("New Task")),
        MenuItem("List Tasks", lambda: print("List Tasks")),
        MenuItem("Logout", lambda: print("Logout"))
    ]
    main_menu = Menu(menu_items, intro_sentence=f"How can I help, {user.name}?")

    next_action = main_menu.run(console)

    next_action()


if __name__ == "__main__":
    main()