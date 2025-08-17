import hashlib
from typing import Literal, Optional

from ..core.types import UserModel
from ..core.utils import parse_message
from ..core.messeger import UNEXPECTED_TYPE
from ..exceptions import UnexpectedTypeException


def _raiser_UTE(e, p, i, t):
    if not isinstance(i, t):
        raise UnexpectedTypeException(parse_message(
            UNEXPECTED_TYPE,
            METHOD="Email(...)",
            EXPECTED=e,
            PARAMETER=p,
            RECEIVED=f"{type(i).__name__} ({i})"
        ))


class Email:
    __slots__ = ["sender", "subject", "content", "attachments", "destination", "date", "rid", "user"]

    def __init__(self, destination: str|list[str], user: Optional[UserModel]=None, sender: Optional[str]=None, subject: Optional[str]=None, content: Optional[str]=None, date: Optional[str]=None, **attachments: dict[str, dict[Literal["content_type", "payload", "main_type", "sub_type"], str]]):
        _raiser_UTE("str|list[str]", "destination", destination, (str, list))
        if user: _raiser_UTE("UserModel", "user", user, UserModel)
        if sender: _raiser_UTE("str", "sender", sender, str)
        if subject: _raiser_UTE("str", "subject", subject, str)
        if content: _raiser_UTE("str", "content", content, str)
        if date: _raiser_UTE("str", "date", date, str)
        if attachments: 
            for name, att in attachments.items: _raiser_UTE("dict", name, att, dict)
        
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
