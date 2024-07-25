from entities.message import Message

class Session:

    def __init__(self, session_id) -> None:
        self.session_id = session_id
        self.messages = []