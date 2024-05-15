from abc import ABC, abstractmethod
from typing import List

class EmailSender(ABC):

    @abstractmethod
    def send_email(self, subject: str, recipients: List[str], body: str):
        pass