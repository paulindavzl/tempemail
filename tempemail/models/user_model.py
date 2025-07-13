from typing import Optional

from ..core import utils
from ..core.env_handler import EnvHandler


_ENV = EnvHandler.unique()


class UserModel:
    def __init__(self, name: Optional[str]=None, email: Optional[str]=None):
        self.temp_name = name if name is not None else utils.gen_anonymous_name()
        self.temp_email = email if email is not None else self._get_email()


    def _get_email(self) -> str:
        email = f"{self.temp_name}@{_ENV.SERVER}.com"

        return email
    

    def copy(self) -> "UserModel":
        return UserModel(**self.to_dict)


    @property
    def to_dict(self) -> dict:
        resp = {
            "name": self.temp_name,
            "email": self.temp_email
        }

        return resp
    

    def __str__(self) -> str:
        return f"username: {self.temp_name}, email: {self.temp_email}"
    

    def __repr__(self):
        return f"<UserModel: {self.temp_name} <{self.temp_email}>>"