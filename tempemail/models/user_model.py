import time
import string
import random as rd
from typing import Optional

from ..core.env_handler import EnvHandler
from ..core.messeger import DEFAULT_NAME


_ENV: EnvHandler


_LETTERS = list(string.ascii_letters)
_NUMBERS = list(string.digits)
_CHARS = _LETTERS + _NUMBERS


class UserModel:
    __slots__ = ["name", "email"]

    def __init__(self, env: str|EnvHandler, name: Optional[str]=None, email: Optional[str]=None):
        """
        modelo do usuário.

        ### parâmetros:

            env (str|EnvHandler): caminho para o arquivo ou instância do manipulador de variáveis de ambiente
            name (Optional[str]): nome do usuário
            email (Optional[str]): e-mail do usuário
        """
        _ENV = EnvHandler.unique(env) if isinstance(env, str) else env

        self.temp_name = name if name is not None else self._gen_anonymous_name()
        self.temp_email = email if email is not None else self._get_email()


    def _get_email(self) -> str:
        email = f"{self.temp_name}@{_ENV.SERVER}.com"

        return email
    

    def _gen_anonymous_name(name: str=DEFAULT_NAME, add_time: bool=True, ranger: int=10) -> str:
        name += "_"
        for _ in range(ranger):
            name += str(rd.choice(_CHARS))

        if add_time:
            name += f"_{time.time()}"

        return name
        

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