from rich.console import Console
from views.menu import Menu
from services.auth import login

def main():
    console = Console()
    # user login
    user = login()

    menu_items = ["List Tasks", "New Task"]
    main_menu = Menu(menu_items, intro_sentence=f"How can I help, {user.name}?")

    main_menu.display(console)


if __name__ == "__main__":
    main()