import os
import dotenv 
from typing import TypeAlias, Literal, Optional

from . import utils
from ..exceptions import EnvironmentVariableRequiredException, EmptyEnvfileException
from .messeger import (
    MISSING_VARIABLE, 
    EMPTY_ENVFILE
)

_REQUIRED: TypeAlias = Literal["__REQUIRED__"]
_COMMON: TypeAlias = Literal["__COMMON__"]


class EnvHandler:
    """
    classe responsável por manipular variáveis de ambientes.

    ### métodos:

        def get_all_variables(self) -> None: carrega todas as variáveis de ambiente no arquivo "*.env" (arquivo pré-definido)

        def load(self) -> None: carrega as variáveis de ambiente já pré-definidas por EnvHandler.set_env(...) ou EnvHandler.get_all_variables()

        def set_env(self, reload: bool=True, **envdata: str|dict[Literal["value", "rule"], Literal["common", "required"]]) -> None: define quais variáveis de ambiente serão carregadas e define/altera o valor delas no arquivo "*.env"

        def set_default(self, exists_ok: bool=True, reload: bool=True): define todas as variáveis para os valores padrões

        @classmethod
        def unique(cls, envfile: str=".env") -> EnvHandler: retorna uma instância única e global de EnvHandler

    ### uso básico:

        env = EnvHandler.unique(envfile="my_envfile.env") # obtém uma instância única da classe EnvHandler
        env.load() # carrega/recarrega as variáveis de ambiente

        print(env.HOST) # "localhost" (valor padrão)

        env.set_env(
            REQUIRED_KEY={"rule": "required", "value": "my_required_key_123"}, # define uma variável de ambiente obrigatória
            COMMON_KEY="my_common_key_123" # define uma variável de ambiente comum
        )

        print(env.REQUIRED_KEY) # "my_required_key_123"
        print(env.COMMON_KEY) # "my_common_key_123"

    """

    __instance__: dict[str, "EnvHandler"]
    __expecteds__: dict[str, dict[Literal["rule", "default"]]] = {
        "SERVER": {"rule": _REQUIRED, "default": None}, 
        "PORT": {"rule": _REQUIRED, "default": None}
    }

    SERVER: str
    PORT: str

    def __init__(self, envfile: str=".env"):
        """
        cria uma nova instância de EnvHandler.

        ### parâmetros:

            envfile (str): localização do arquivo ".env" (diferentes envfiles retornam instâncias diferentes)
        """
        self._envfile = envfile
        self.set_default(exists_ok=True, reload=False)


    def get_all_variables(self):
        """
        carrega todas as variáveis de ambiente no arquivo "*.env" (arquivo pré-definido).

        ### uso:

            # exemplo de arquivo .env:
                SERVER='localhost'
                PORT='1025'
                SECRET_KEY='my_secret_key_123'
                TOKEN='my_token_123'


            env = EnvHandler.unique(envfile="my_envfile.env")
            
            env.get_all_variables()

            print(env.SECRET_KEY) # "my_secret_key_123"
            print(env.TOKEN) # "my_token_123"
        """
        envs = {}
        with open(self._envfile, "w") as envfile:
            envfile_content = envfile.readlines()

            for line in envfile_content:
                line_splited = line.split("=")
                envs[line_splited[0]] = line_splited[1].replace("'", "").strip()

        self.set_env(**envs)

        self.load()


    def load(self):
        """
        carrega as variáveis de ambiente já pré-definidas por EnvHandler.set_env(...) ou EnvHandler.get_all_variables()

        ### uso:

            env = EnvHandler.unique(envfile="my_envfile.env")

            env.load() carrega as variáveis de ambiente já pré-definidas por EnvHandler.set_env(...) ou EnvHandler.get_all_variables()

            print(env.VARIABLE) # "variable_value"
        """
        dotenv.load_dotenv(
            self._envfile,
            override=True
        )

        for envname, info in self.__expecteds__.items():
            rule = info["rule"]
            default = info["default"]

            value = os.getenv(envname, default)

            if not value and rule is _REQUIRED:
                raise EnvironmentVariableRequiredException(utils.parse_message(MISSING_VARIABLE, NAME=envname))
            
            setattr(self, envname, value)


    def set_env(self, reload: bool=True, **envdata: str|dict[Literal["value", "rule"], Literal["common", "required"]]):
        """
        define quais variáveis de ambiente serão carregadas e define/altera o valor delas no arquivo "*.env".

        ### parâmetros:

            reload (bool): define se recarrega automaticamente ao adicionar as variáveis
            envdata (dict[str, str|dict[Literal["value", "rule"], Literal["common", "required"]]]): informações da variável que será definida

        ### uso:

            env = EnvHandler.unique(envfile="my_envfile.env")

            env.set_env(
                REQUIRED_KEY={"rule": "required", "value": "my_required_key_123"}, # adiciona uma variável obrigatória
                COMMON_KEY="my_common_key_123", # adiciona uma variável "comum" (não obrigatória)
                OTHER_COMMON_KEY={"rule": "common", "value": "my_other_common_key_123"} # outra forma de adicionar uma variável comum
            )

        ### observação:

            - EnvHandler.set_env(...) define uma variável no arquivo ".env" ou altera seu valor caso ela já exista

            - se uma variável obrigatória for None ou possuir um valor vazio (""), ocorrerá um erro ao usar EnvHandler.load() -> EnvironmentVariableRequiredException

        """
        for envname, value in envdata.items():
            rule = "common"
            if isinstance(value, dict):
                rule = value["rule"]
                value = value["value"]

            if envname not in self.__expecteds__:
                self.__expecteds__[envname] = {"rule": _REQUIRED, "default": None} if rule == "required" else {"rule": _COMMON, "default": value}

            dotenv.set_key(self._envfile, envname, str(value))
            
        if reload:
            self.load()


    def set_default(self, exists_ok: bool=True, reload: bool=True):
        """
        define todas as variáveis para os valores padrões.

        ### parâmetros:

            exists_ok (bool): quando True, se o arquivo "*.env" já existir, não redefine os valores para o padrão
            reload (bool): define se recarrega automaticamente ao adicionar as variáveis

        ### uso:

            env = EnvHandler.unique(envfile="my_envfile.env")

            env.set_default(exists_ok=True) # caso o arquivo "my_envfile.env" não exista, ele será criado com as variáveis no valor padrão
        """
        def _get_envs() -> dict:
            _envs = {}
            for envname, info in self.__expecteds__.items():
                rule = info["rule"]
                value = info["default"] if rule is _COMMON else ""

                _envs[envname] = value

            return _envs

        if not os.path.exists(self._envfile):
            with open(self._envfile, "w"):
                pass

            self.set_env(**_get_envs(), reload=False)

        elif not exists_ok:
            self.set_env(**_get_envs(), reload=False)

        if reload:
            self.load()


    @classmethod
    def unique(cls, envfile: Optional[str]=None) -> "EnvHandler":
        """
        retorna uma instância única e global de EnvHandler.

        ### parâmetros:

            envfile (str): localização do arquivo ".env" (diferentes envfiles retornam instâncias diferentes)

        ### uso:

            env = EnvHandler.unique(envfile="my_envfile.env")

        ### observação:

            - caso envfile não for informado, qualquer instância será retornada e se não houver instância, um erro será gerado.
        """
        if not hasattr(cls, "__instance__"):
            if envfile is None:
                raise EmptyEnvfileException(EMPTY_ENVFILE)
            instance = cls(envfile)
            cls.__instance__ = {envfile: instance}

            return instance
        
        if envfile is None:
            keys = list(cls.__instance__.keys())
            first_key = keys[0]

            instance = cls.__instance__[first_key]
            return instance
        
        instance = cls.__instance__.get(envfile)

        if instance is None:
            instance = cls(envfile)
            cls.__instance__[envfile] = instance

        return instance
        
        
