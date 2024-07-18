from textual.widgets import Button
from textual.widget import Widget
from textual.containers import ScrollableContainer


class MenuItem(Button):
    def __init__(self, name: str, widget: Widget, id: str=None, classes=None) -> None:
        self.widget = widget
        super().__init__(name, id=id if id else name.lower().replace(" ", "_"), classes=classes)
        self.styles.width='100%'


class Menu(ScrollableContainer):

    def __init__(self, menu_items: list[MenuItem], id: str) -> None:
        self.menu_items = menu_items
        super().__init__(id=id)


    def compose(self):
        for item in self.menu_items:
            yield item

    
