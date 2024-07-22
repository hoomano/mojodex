class PartialMessage:
    def __init__(self, message: str, author: str, is_draft: bool = False) -> None:
        self.message = message
        self.author = author
        self.is_draft = is_draft
        self.icon = "👤" if author == "user" else "🤖"

class Message(PartialMessage):
    def __init__(self, pk: int, message: str, author: str, is_draft: bool = False) -> None:
        self.pk = pk
        super().__init__(message, author, is_draft)
