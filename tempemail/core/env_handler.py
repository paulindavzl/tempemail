import os
import dotenv 
from typing import TypeVar

from . import utils
from .controller import (
    MISSING_VARIABLE
)

_REQUIRED = TypeVar("_REQUIRED")


class EnvHandler:
    """
    classe responsável por manipular variáveis de ambientes
    """

    __instance__: dict[str, "EnvHandler"]
    __expecteds__ = {"SERVER": _REQUIRED, "PORT": _REQUIRED}

    SERVER: str
    PORT: str

    def __init__(self, envfile: str=".env"):
        self._envfile = envfile
        self.set_default(True)


    def load(self):
        dotenv.load_dotenv(
            self._envfile,
            override=True
        )

        for envname, default in self.__expecteds__.items():
            value = os.getenv(envname, default)

            if value is _REQUIRED:
                raise EnvironmentError(utils.parse_message(
                    MISSING_VARIABLE,
                    NAME=envname
                ))
            
            setattr(self, envname, value)


    def set_env(self, **envnames):
        for envname, value in envnames.items():
            value = str(value)

            if envname not in self.__expecteds__:
                self.__expecteds__[envname] = value

            dotenv.set_key(self._envfile, envname, "" if value is _REQUIRED else value)
            setattr(self, envname, value)


    def set_default(self, exists_ok: bool=True, reload: bool=True):
        if not os.path.exists(self._envfile):
            with open(self._envfile, "w"):
                pass

            self.set_env(**self.__expecteds__)

        if not exists_ok:
            self.set_env(**self.__expecteds__)


        if reload:
            self.load()


    @classmethod
    def unique(cls, envfile: str=".env") -> "EnvHandler":
        if not hasattr(cls, "__instance__"):
            instance = cls(envfile)
            cls.__instance__ = {envfile: instance}

            return instance
        
        instance = cls.__instance__.get(envfile)

        if instance is None:
            instance = cls(envfile)
            cls.__instance__[envfile] = instance

        return instance
        
        
