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

        self.rid = hashlib.sha256(
            sender.encode()
            +"".join(destination).encode()
            +str(date).encode()
        ).hexdigest() if date and sender else None
