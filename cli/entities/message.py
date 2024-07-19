class PartialMessage:
    def __init__(self, message: str, author: str) -> None:
        self.message = message
        self.author = author
        self.icon = "👤" if author == "user" else "🤖"

class Message(PartialMessage):
    def __init__(self, pk: int, message: str, author: str) -> None:
        self.pk = pk
        super().__init__(message, author)
