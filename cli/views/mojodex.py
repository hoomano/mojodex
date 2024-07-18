from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Header, Static, Button
from textual.containers import Vertical
from textual.reactive import reactive
from textual.keys import Keys

class MenuItem(Button):
    def __init__(self, name: str, action: callable, id: str=None):
        self.action = action
        super().__init__(name, id=id if id else name.lower().replace(" ", "_"))


class Menu(Widget):

    def __init__(self, menu_items: list[MenuItem], id: str) -> None:
        self.menu_items = menu_items
        super().__init__(id=id)


    def compose(self):
        for item in self.menu_items:
            yield item


class Mojodex(App):
    CSS_PATH = "dock_layout3_sidebar_header.tcss"

    focused_index = reactive(0)

    def __init__(self, menu) -> None:
        self.menu = menu
        self.current_page_id = "body"
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header(id="header")
        with Vertical(id="sidebar"):
            yield self.menu
        yield Static("CONTENT", id="body")

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
            action = event.button.action
            body = self.query_one(f"#{self.current_page_id}", Widget)
            body.remove()
            current_page = action()
            self.current_page_id = current_page.id
            self.mount(current_page)

