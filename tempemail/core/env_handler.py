import os
import dotenv 
from typing import TypeAlias, Literal, Optional

from .utils import parse_message, Path
from ..exceptions import *
from .messeger import (
    MISSING_VARIABLE, 
    EMPTY_ENVFILE,
    UNEXPECTED_TYPE,
    UNEXPECTED_RULE
)

_REQUIRED: TypeAlias = Literal["__REQUIRED__"]
_COMMON: TypeAlias = Literal["__COMMON__"]


_DEFAULT_PATH = Path(".env")
class EnvHandler:
    """
    classe responsável por manipular variáveis de ambientes.

    ### métodos:

        def get_all_variables(self) -> None: carrega todas as variáveis de ambiente no arquivo "*.env" (arquivo pré-definido)

        def load(self) -> None: carrega as variáveis de ambiente já pré-definidas por EnvHandler.set_env(...) ou EnvHandler.get_all_variables()

        def set_env(self, reload: bool=True, **envdata: str|dict[Literal["value", "rule"], Literal["common", "required"]]) -> None: define quais variáveis de ambiente serão carregadas e define/altera o valor delas no arquivo "*.env"

        def set_default(self, exists_ok: bool=True, reload: bool=True): define todas as variáveis para os valores padrões

        @classmethod
        def unique(cls, envpath: str=".env") -> EnvHandler: retorna uma instância única e global de EnvHandler

    ### uso básico:

        path = Path("my_envpath.env")
        env = EnvHandler.unique(envpath=path) # obtém uma instância única da classe EnvHandler
        env.load() # carrega/recarrega as variáveis de ambiente

        env.set_env(
            REQUIRED_KEY={"rule": "required", "value": "my_required_key_123"}, # define uma variável de ambiente obrigatória
            COMMON_KEY="my_common_key_123" # define uma variável de ambiente comum
        )

        print(env.REQUIRED_KEY) # "my_required_key_123"
        print(env.COMMON_KEY) # "my_common_key_123"

    """

    __instance__: dict[str, "EnvHandler"] = {}

    SERVER: str
    PORT: str

    def __init__(self, envpath: Path=_DEFAULT_PATH):
        """
        cria uma nova instância de EnvHandler.

        ### parâmetros:

            envpath (Path): localização do arquivo ".env" (diferentes envpaths retornam instâncias diferentes)
        """
        if not isinstance(envpath, Path):
            raise UnexpectedTypeException(parse_message(
                UNEXPECTED_TYPE,
                METHOD="EnvHandler(...)",
                EXPECTED="Path",
                PARAMETER="envpath",
                RECEIVED=f"{type(envpath).__name__} ({envpath})"
            ))
        
        self.__expecteds__: dict[str, dict[Literal["rule", "default"]]] = {
            "SERVER": {"rule": _REQUIRED, "default": None}, 
            "PORT": {"rule": _REQUIRED, "default": None}
        }
        self._envpath = envpath
        self.set_default(exists_ok=True, reload=False)

        self._set_unique_instance(str(envpath), self)


    def get_all_variables(self):
        """
        carrega todas as variáveis de ambiente no arquivo "*.env" (arquivo pré-definido).

        ### uso:

            # exemplo de arquivo .env:
                SERVER='localhost'
                PORT='1025'
                SECRET_KEY='my_secret_key_123'
                TOKEN='my_token_123'


            path = Path("my_envpath.env")
            env = EnvHandler.unique(envpath=path)
            
            env.get_all_variables()

            print(env.SECRET_KEY) # "my_secret_key_123"
            print(env.TOKEN) # "my_token_123"
        """
        envs = {}
        with self._envpath.file() as envpath:
            envpath_content = envpath.readlines()

            for line in envpath_content:
                if len(line) >= 3 and "=" in line:
                    line_splited = line.split("=")
                    envs[line_splited[0]] = line_splited[1].replace("'", "").strip()

        self.set_env(**envs)

        self.load()


    def load(self):
        """
        carrega as variáveis de ambiente já pré-definidas por EnvHandler.set_env(...) ou EnvHandler.get_all_variables()

        ### uso:

            path = Path("my_envpath.env")
            env = EnvHandler.unique(envpath=path)

            env.load() carrega as variáveis de ambiente já pré-definidas por EnvHandler.set_env(...) ou EnvHandler.get_all_variables()

            print(env.VARIABLE) # "variable_value"
        """
        dotenv.load_dotenv(
            str(self._envpath),
            override=True
        )

        for envname, info in self.__expecteds__.items():
            rule = info["rule"]
            default = info["default"]

            value = os.getenv(envname, default)

            if not value and rule is _REQUIRED:
                raise EnvironmentVariableRequiredException(parse_message(MISSING_VARIABLE, NAME=envname))
            
            setattr(self, envname, value)


    def set_env(self, reload: bool=True, setteds_ok: bool=True, **envdata: str|dict[Literal["value", "rule"], Literal["common", "required"]]):
        """
        define quais variáveis de ambiente serão carregadas e define/altera o valor delas no arquivo "*.env".

        ### parâmetros:

            reload (bool): define se recarrega automaticamente ao adicionar as variáveis
            setteds_ok (bool): caso True, se uma variável já estiver carregada, suas regras não são alteradas
            envdata (dict[str, str|dict[Literal["value", "rule"], Literal["common", "required"]]]): informações da variável que será definida

        ### uso:

            path = Path("my_envpath.env")
            env = EnvHandler.unique(envpath=path)

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

                if rule not in ["common", "required"]:
                    raise UnexpectedValueException(parse_message(UNEXPECTED_RULE, RULE=rule))
                value = value["value"]

            if envname not in self.__expecteds__ or not setteds_ok:
                self.__expecteds__[envname] = {"rule": _REQUIRED, "default": None} if rule == "required" else {"rule": _COMMON, "default": value}

            dotenv.set_key(str(self._envpath), envname, str(value))
            
        if reload:
            self.load()


    def set_default(self, exists_ok: bool=True, reload: bool=True):
        """
        define todas as variáveis para os valores padrões.

        ### parâmetros:

            exists_ok (bool): quando True, se o arquivo "*.env" já existir, não redefine os valores para o padrão
            reload (bool): define se recarrega automaticamente ao adicionar as variáveis

        ### uso:

            path = Path("my_envpath.env")
            env = EnvHandler.unique(envpath=path)

            env.set_default(exists_ok=True) # caso o arquivo "my_envpath.env" não exista, ele será criado com as variáveis no valor padrão
        """
        def _get_envs() -> dict:
            _envs = {}
            for envname, info in self.__expecteds__.items():
                rule = info["rule"]
                value = info["default"] if rule is _COMMON else ""

                _envs[envname] = value

            return _envs

        if not self._envpath.exists:
            with self._envpath.file("w", True):
                pass

            self.set_env(**_get_envs(), reload=False)

        elif not exists_ok:
            self.set_env(**_get_envs(), reload=False)

        if reload:
            self.load()


    @classmethod
    def _set_unique_instance(cls, envpath: str, instance: "EnvHandler"):
        if not cls.__instance__:
            if envpath is None:
                raise EmptyEnvpathException(EMPTY_ENVFILE)
            cls.__instance__ = {envpath: instance}
            return
        
        cls.__instance__[str(envpath)] = instance


    @classmethod
    def unique(cls, envpath: Optional[Path]=None) -> "EnvHandler":
        """
        retorna uma instância única e global de EnvHandler.

        ### parâmetros:

            envpath (Path): localização do arquivo ".env" (diferentes envpaths retornam instâncias diferentes)

        ### uso:

            path = Path("my_envpath.env")
            env = EnvHandler.unique(envpath=path)

        ### observação:

            - caso envpath não for informado, qualquer instância será retornada e se não houver instância, um erro será gerado.
        """
        if envpath and not isinstance(envpath, Path):
            raise UnexpectedTypeException(parse_message(
                UNEXPECTED_TYPE,
                METHOD="EnvHandler(...)",
                EXPECTED="Path",
                PARAMETER="envpath",
                RECEIVED=f"{type(envpath)} ({envpath})"
            ))     
        if envpath is None:
            keys = list(cls.__instance__.keys())
            first_key = keys[0]

            instance = cls.__instance__[first_key]
            return instance
        
        instance = cls.__instance__.get(str(envpath))

        if instance is None:
            instance = cls(envpath)

        cls._set_unique_instance(str(envpath), instance)

        return instance
        
        
    def __str__(self):
        return str(self._envpath)
    

    def __repr__(self):
        return f"<EnvHandler: {self._envpath}>"