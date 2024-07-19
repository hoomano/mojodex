
class Message:
    def __init__(self, pk: int, message: str, author: str) -> None:
        self.pk = pk
        self.message = message
        self.author = author
        self.icon = "👤" if author == "user" else "🤖"