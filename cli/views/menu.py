from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
import termios, tty, sys


class MenuItem:
    def __init__(self, name: str, action: callable):
        self.name = name
        self.action = action
    
    def __str__(self):
        return self.name

class Menu:

    def __init__(self, items: list[MenuItem], intro_sentence: str):
        self.items = items
        self.current_selection = 0
        self.intro_sentence = intro_sentence

    def display_menu(self, console: Console):
        console.clear()
        console.print(self.intro_sentence, style="bold blue")
        for idx, item in enumerate(self.items):
            if idx == self.current_selection:
                console.print(Panel(Text(item.name, style="bold green"), border_style="green", title="Selected"))
            else:
                console.print(Panel(item.name, border_style="white"))

    @staticmethod
    def __get_key():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # Handle escape sequences
                ch += sys.stdin.read(2)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def run(self, console: Console) -> callable:
        try: 
            action = lambda: None
            with Live(auto_refresh=False) as live:
                self.display_menu(console)
                while True:
                    key = Menu.__get_key()
                    if key == '\x1b[A':  # Up arrow key
                        self.current_selection = (self.current_selection - 1) % len(self.items)
                    elif key == '\x1b[B':  # Down arrow key
                        self.current_selection = (self.current_selection + 1) % len(self.items)
                    elif key == '\n' or key == '\r':  # Enter key
                        return self.items[self.current_selection].action
                    elif key == 'q':
                        return action
                    self.display_menu(console)
        except Exception as e:
            console.print(f"An error occurred: {e}", style="bold red")
            return action