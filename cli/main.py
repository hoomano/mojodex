from rich.console import Console
from views.menu import Menu, MenuItem
from services.auth import login

user = None
console = None

def display_task_list():
    global user
    task_execution_list = user.load_task_execution_list()

    menu_items = [
        MenuItem(f"{task.icon} {task.title}\n\n{task.summary}\n\n{task.duration_ago} {'✅' if task.produced_text_done else ''}", lambda: print(f"Task: {task.title}"))
        for task in task_execution_list
    ]
    task_menu = Menu(menu_items, intro_sentence="Select a task to view more details:")

    next_action = task_menu.run(console)

    next_action()

def main():
    
    global console
    console = Console()

    global user 
    user = login()

    menu_items = [
        MenuItem("New Task", lambda: print("New Task")),
        MenuItem("List Tasks", display_task_list),
        MenuItem("Logout", lambda: print("Logout"))
    ]
    main_menu = Menu(menu_items, intro_sentence=f"How can I help, {user.name}?")

    next_action = main_menu.run(console)

    next_action()


if __name__ == "__main__":
    main()