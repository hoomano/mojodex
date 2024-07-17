from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live




class Menu:

    def __init__(self, items: list[str], intro_sentence: str):
        self.items = items
        self.current_selection = 0
        self.intro_sentence = intro_sentence

    def display_menu(self, console: Console):
        console.clear()
        console.print(self.intro_sentence, style="bold blue")
        for idx, item in enumerate(self.items):
            if idx == self.current_selection:
                console.print(Panel(Text(item, style="bold green"), border_style="green", title="Selected"))
            else:
                console.print(Panel(item, border_style="white"))

    def get_key(self):
        import termios, tty, sys
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

    def display(self, console: Console):
        with Live(auto_refresh=False) as live:
            self.display_menu(console)
            while True:
                key = self.get_key()
                if key == '\x1b[A':  # Up arrow key
                    self.current_selection = (self.current_selection - 1) % len(self.items)
                elif key == '\x1b[B':  # Down arrow key
                    self.current_selection = (self.current_selection + 1) % len(self.items)
                elif key == '\n' or key == '\r':  # Enter key
                    console.print(f"You selected: {self.items[self.current_selection]}", style="bold green")
                    break
                elif key == 'q':
                    break
                self.display_menu(console)
