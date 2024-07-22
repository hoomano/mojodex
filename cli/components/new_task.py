from textual.widget import Widget
from textual.widgets import Input
from services.user_services import load_user_tasks_list
from components.run_task import RunTaskLayout
from components.menu import Menu, MenuItem
from entities.user_task import UserTaskListElementDisplay
from textual.app import ComposeResult
import threading

class NewTaskMenuItem(MenuItem):
    def __init__(self, user_task: UserTaskListElementDisplay, action: callable, classes=None) -> None:
        self.user_task_pk = user_task.pk
        super().__init__(str(user_task), action, classes=classes)

class NewTaskLayout(Widget):

    def __init__(self, id: str) -> None:
        
        self.user_tasks: list[UserTaskListElementDisplay] = load_user_tasks_list()

        self.menu = Menu(
        [
            NewTaskMenuItem(
                user_task, 
                lambda user_task_pk: RunTaskLayout(user_task_pk)
                )
            for user_task in self.user_tasks
        ]
    )
        for menu_item in self.menu.menu_items:
            menu_item.styles.height="8"
            menu_item.styles.margin=1

        self.search_input = Input(placeholder="Search for tasks", id="search_input")

        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        yield self.search_input
        yield self.menu

    def on_mount(self) -> None:
        self.search_input.focus()

    def on_button_pressed(self, event: NewTaskMenuItem.Pressed) -> None:
        if isinstance(event.button, NewTaskMenuItem):
            menu_item = event.button
            if menu_item.id in [item.id for item in self.menu.menu_items]:
                self.menu.remove()
                widget = menu_item.action(menu_item.user_task_pk)
                self.mount(widget)
                self.search_input.remove()

    def on_input_changed(self, event: Input.Changed):
        
        if event.value == "":
            self._update_menu(self.user_tasks)
            return
        from textual.fuzzy import Matcher
        matcher = Matcher(query=event.value)
        ordered_user_tasks = [{
            'user_task': user_task,
            'score': matcher.match(f"{user_task.name}\n{user_task.description}")} for user_task in self.user_tasks]
        # order the list by score
        ordered_user_tasks.sort(key=lambda x: x['score'], reverse=True)
        
        list_user_tasks = [item['user_task'] for item in ordered_user_tasks if item['score'] > 0.5]
        
        self._update_menu(list_user_tasks)


    def _update_menu(self, list_user_tasks):

        self.menu.remove()

        new_menu_thread = threading.Thread(target=self._mount_new_menu, args=( [
                NewTaskMenuItem(
                    user_task, 
                    lambda user_task_pk: RunTaskLayout(user_task_pk)
                    )
                for user_task in list_user_tasks
            ], ))
        new_menu_thread.start()
        

    def _mount_new_menu(self, new_items: list[NewTaskMenuItem]):
        try:
            self.menu = Menu(new_items)
            self.app.call_from_thread(lambda: self.mount(self.menu))
            
            for menu_item in self.menu.menu_items:
                menu_item.styles.height="8"
                menu_item.styles.margin=1
        except Exception as e:
            self.notify(f"Error: {e}", severity="error", title="Error")




        
