from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Header, Static
from textual.containers import Vertical
from textual.reactive import reactive
from textual.keys import Keys
import threading

from components.menu import Menu, MenuItem

class Mojodex(App):
    CSS_PATH = "style.tcss"

    focused_index = reactive(0)

    def __init__(self, menu) -> None:
        self.menu : Menu = menu
        self._initial_page = "body"
        self.current_page_id =self._initial_page
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header(id="header")
        with Vertical(id="sidebar"):
            yield self.menu
        yield Static("CONTENT", id=self._initial_page)

    def on_mount(self) -> None:
        self.focus_option(0)  # Initially focus the first button

    def focus_option(self, index: int) -> None:
        buttons = self.query("#sidebar Button")
        if 0 <= index < len(buttons):
            buttons[index].focus()
            self.focused_index = index

    def on_key(self, event) -> None:
        if event.key == Keys.Up:
            self.focus_option((self.focused_index - 1) % 3)
        elif event.key == Keys.Down:
            self.focus_option((self.focused_index + 1) % 3)

    def on_button_pressed(self, event: MenuItem.Pressed) -> None:
        if isinstance(event.button, MenuItem):
            menu_item = event.button
            if menu_item.id in [item.id for item in self.menu.menu_items]:
                body = self.query_one(f"#{self.current_page_id}", Widget)
                body.remove()

                menu_item_action_thread = threading.Thread(target=self._mount_menu_item, args=(menu_item,))
                menu_item_action_thread.start()
                
    
    def _mount_menu_item(self, menu_item):
        widget = menu_item.action()
        self.current_page_id = widget.id
        self.app.call_from_thread(lambda: self.mount(widget))

