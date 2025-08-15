import hashlib
from typing import Literal, Optional

from ..core.types import UserModel


class Email:
    __slots__ = ["sender", "subject", "content", "attachments", "destination", "date", "rid", "user"]

    def __init__(self, destination: str|list[str], user: Optional[UserModel]=None, sender: Optional[str]=None, subject: Optional[str]=None, content: Optional[str]=None, date: Optional[str]=None, **attachments: dict[str, dict[Literal["content_type", "payload", "main_type", "sub_type"], str]]):
        self.destination = destination
        self.user = user.copy() if user else None
        self.sender = f"{user.temp_name} <{user.temp_email}>" if user else sender
        self.subject = subject
        self.content = content
        self.date = date
        self.attachments = attachments or {}

        self.gen_rid()
        

    def gen_rid(self):
        self.rid = hashlib.sha256(
            self.sender.encode()
            +"".join(self.destination).encode()
            +str(self.date).encode()
            +str(self.subject).encode()
            +str(self.content).encode()
        ).hexdigest() if self.date and self.sender else None
