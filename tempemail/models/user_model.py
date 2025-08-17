import time
import string
import random as rd
from typing import Optional

from ..core.utils import parse_message
from ..core.env_handler import EnvHandler
from ..exceptions import UnexpectedTypeException
from ..core.messeger import DEFAULT_NAME, UNEXPECTED_TYPE


_LETTERS = list(string.ascii_letters)
_NUMBERS = list(string.digits)
_CHARS = _LETTERS + _NUMBERS


def _raiser_UTE(p, i, t):
    if not isinstance(i, t):
        raise UnexpectedTypeException(parse_message(
            UNEXPECTED_TYPE,
            METHOD="UserModel(...)",
            EXPECTED=t.__name__,
            PARAMETER=p,
            RECEIVED=f"{type(i).__name__} ({i})"
        ))


class UserModel:
    __slots__ = ["temp_name", "temp_email", "_env"]

    temp_email: str
    temp_name: str
    _env: EnvHandler

    def __init__(self, env: EnvHandler, name: Optional[str]=None, email: Optional[str]=None):
        """
        modelo do usuário.

        ### parâmetros:

            env (EnvHandler): instância do manipulador de variáveis de ambiente
            name (Optional[str]): nome do usuário
            email (Optional[str]): e-mail do usuário
        """
        _raiser_UTE("env", env, EnvHandler)
        if name: _raiser_UTE("name", name, str)
        if email: _raiser_UTE("email", email, str)
        
        self._env = env
        self.temp_name = name if name is not None else self._gen_anonymous_name()
        self.temp_email = email if email is not None else self._get_email()


    def _get_email(self) -> str:
        email = f"{self.temp_name}@{self._env.SERVER}.com"

        return email
    

    def _gen_anonymous_name(name: str=DEFAULT_NAME, add_time: bool=True, ranger: int=10) -> str:
        name = DEFAULT_NAME + "_"
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