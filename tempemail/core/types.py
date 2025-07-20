from typing import Optional, Literal

class UserModel:
    name: str
    email: str
    to_dict: dict
    def copy() -> "UserModel": ...


class Email:
     destination: str|list[str]
     user: Optional[UserModel]=None, 
     sender: Optional[str]=None, 
     subject: Optional[str]=None, 
     content: Optional[str]=None, 
     date: Optional[str]=None, 
     attachments: dict[str, dict[Literal["content_type", "payload", "main_type", "sub_type"], str]]