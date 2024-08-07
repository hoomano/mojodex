from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Header, Footer
from textual.containers import Vertical
from textual.reactive import reactive
from textual.keys import Keys
from textual.binding import Binding

import threading

from components.menu import Menu, MenuItem


class Mojodex(App):
    CSS_PATH = "style.tcss"
    BINDINGS= [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="n", action="new_task", description="New Task")
               ]
    def action_new_task(self):
        try:
            # go to new task screen            
            self.navigate(self.menu.menu_items[0])
            self.current_menu = self.menu
            self.focus_option(0)
        except Exception as e:
            self.notify(f"Error: {e}")


    def action_quit(self):
        self.app.exit()

    focused_index = reactive(0)

    def __init__(self, menu) -> None:
        self.menu : Menu = menu
        super().__init__()
        self.initial_widget = self.menu.menu_items[1].action()
        self.current_page_id = self.initial_widget.id
        self.current_menu = self.menu

    def compose(self) -> ComposeResult:
        yield Header(id="header")
        with Vertical(id="sidebar"):
            yield self.menu
        yield self.initial_widget
        yield Footer()

    def on_mount(self) -> None:
        self.focus_option(1)  # Initially focus the first button

    def focus_option(self, index: int) -> None:
        if 0 <= index < len(self.current_menu.menu_items):
            self.current_menu.menu_items[index].focus()
            self.focused_index = index

    def on_key(self, event) -> None:
        if event.key == Keys.Up:
            self.focus_option((self.focused_index - 1) % len(self.current_menu.menu_items))
        elif event.key == Keys.Down:
            self.focus_option((self.focused_index + 1) % len(self.current_menu.menu_items))
        elif event.key == Keys.Right:
            try:
                self.current_menu = self.query_one(f"#{self.current_page_id}", Widget).menu if not None else self.menu
            except Exception as e:
                self.notify(f"Error: {e}")
                self.current_menu = self.menu
            self.focus_option(0)
        elif event.key == Keys.Left:
            self.current_menu = self.menu
            self.focus_option(0)

    def on_button_pressed(self, event: MenuItem.Pressed) -> None:
        if isinstance(event.button, MenuItem):
            menu_item = event.button
            if menu_item.id in [item.id for item in self.menu.menu_items]:
                self.navigate(menu_item)

    
    def navigate(self, menu_item):
        try:
            body = self.query_one(f"#{self.current_page_id}", Widget)
            body.remove()

            menu_item_action_thread = threading.Thread(target=self._mount_menu_item, args=(menu_item,))
            menu_item_action_thread.start()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error", title="Error")
                
    
    def _mount_menu_item(self, menu_item):
        try:
            widget = menu_item.action()
            self.current_page_id = widget.id
            self.app.call_from_thread(lambda: self.mount(widget))
        except Exception as e:
            self.notify(f"Error: {e}", severity="error", title="Error")

        

