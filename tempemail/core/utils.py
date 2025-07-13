import os
import re
import json
import time
import types
import string
import typing
import hashlib
import jsonschema
import random as rd

from ..models.email_data import Email
from .controller import (
    DEFAULT_NAME, 
    FILE_NOT_FOUND,
    NOT_DIRECTORY,
    NOT_FILE,
    DIRECTORY_ALREADY_EXISTS,
    _METADATA_SCHEME_JSON
)


_LETTERS = list(string.ascii_letters)
_NUMBERS = list(string.digits)
_CHARS = _LETTERS + _NUMBERS
_OPEN_TEXT_MODE: typing.TypeAlias = typing.Literal['r', 'rb', 'r+', 'rb+', 'w', 'wb', 'w+', 'wb+', 'a', 'ab', 'a+', 'ab+', 'x', 'xb', 'x+', 'xb+']


def gen_anonymous_name(name: str=DEFAULT_NAME, add_time: bool=True, ranger: int=10) -> str:
    name += "_"
    for _ in range(ranger):
        name += str(rd.choice(_CHARS))

    if add_time:
        name += f"_{time.time()}"

    return name


def parse_path(path: str) -> str:
    path = gen_anonymous_name(path, False, 5)

    while os.path.exists(path):
        path = gen_anonymous_name(path, False, 5)

    return path


def get_filename(*parts) -> str:
    filename = re.sub(
        r"[^\w\-_\. ]",
        "_",
        "_".join(list(parts)) if isinstance(parts, tuple) else parts
    ).replace(" ", "_")

    return filename


def parse_message(message: str, **replace: str) -> str:
    for tag, value in replace.items():
        message = message.replace(f"<{tag}>", str(value))

    return message


def get_email_hash(email: Email, ext: str) -> str:
    sha = hashlib.sha256(str("".join([
        email.subject.strip().lower(),
        email.content.strip().lower(),
        email.sender.strip().lower(),
        str(email.destination).strip().lower(),
        email.date.strip().lower()
    ])).encode()).hexdigest()

    return sha


def get_content_in(path: str, mode: str="r", load_method: types.MethodType=None) -> any:
    if not os.path.exists(path):
        raise FileNotFoundError(parse_message(FILE_NOT_FOUND, PATH=path))
    
    content: any
    with open(path, mode) as file:
        content = load_method(file) if load_method else file.read()

    return content


def is_valid_email_in(*paths: str) -> bool:
    path = os.path.join(*paths)

    if not os.path.exists(path):
        raise FileNotFoundError(parse_message(FILE_NOT_FOUND, PATH=path))
    
    meta = os.path.join(path, "metadata.json")
    metadata: dict = get_content_in(meta, load_method=json.load)

    try:
        jsonschema.validate(metadata, _METADATA_SCHEME_JSON)
    except jsonschema.ValidationError:
        return False
    
    attachments: list[dict[str, str]] = metadata.get("attachments")
    if attachments:
        for att in attachments:
            name = att["name"]
            att_path = os.path.join(path, name)
            
            if not os.path.exists(att_path):
                return False
            
            att_content: bytes = get_content_in(att_path, "rb")
            if not hashlib.sha256(att_content) == att["hash"]:
                return False
    
    extension: str = metadata["extension"]

    content_path = os.path.join(path, "content" + extension)
    content: str = get_content_in(content_path)

    sha = hashlib.sha256(str("".join([
        str(metadata.get("subject", "")).strip().lower(),
        content.strip().lower(),
        str(metadata.get("sender", "")).strip().lower(),
        str(metadata.get("destination", "")).strip().lower(),
        str(metadata.get("date", "")).strip().lower()
    ])).encode()).hexdigest()

    return sha == metadata["hash"]


class Path:
    """
    classe baseada na biblioteca "os", representa um caminho que pode referenciar diretórios ou arquivos

    ### métodos:

        def join(self, in_self: bool=False, *paths: str) -> None: adiciona um componente ao caminho já representado

        def exists(self) -> bool: verifica se o caminho representado existe

        def file(self, mode: _OPEN_TEXT_MODE="r", non_existent_ok: bool=False) -> TextIO: abre um arquivo e retorna-o, possibilitando manipulação

        def items(self) -> list[Path]: retorna todos os componentes do diretório do caminho representado e retorna-os representados em Path

        def mkdir(self, exists_ok: bool=False): cria todos os arquivos do caminho representado caso não existam

        def get_not_existent_name(self, *paths) -> Path: retorna o caminho representado com um nome novo, evitando conflitos com arquivos já existentes

    ### uso:

        path = Path(".", "project_name", "directory")

        print(path) # "./project_name/directory/

        print(path.exists()) # True | False

        path.mkdir() # cria todos os arquivos caso não existam, desde de "project_name" até "directory"

        path.join("subdirectory", in_self=True) # adiciona outro componente na mesma classe

        print(path) # "./project_name/directory/subdirectory/"

        file = path.join("file.txt") # adiciona outro componente e retorna um nova classe

        print(file) # "./project_name/directory/subdirectory/file.txt"
    """

    __slots__ = ["_paths"]

    def __init__(self, *paths: str):
        self._paths = Path._parse_path(paths)


    @staticmethod
    def _parse_path(paths: str|tuple[str]) -> list[str]:
        paths = list(paths) if isinstance(paths, tuple) else [paths]
        return paths


    @typing.overload
    def join(self, /, *paths: str) -> "Path": ...

    @typing.overload
    def join(self, in_self: bool, *paths: str) -> None: ...

    def join(self, *paths: str, **param: bool):
        paths = [str(self)] + Path._parse_path(paths)
        if not param.get("in_self", False):
            path = Path(*paths)
            return path
        
        self._paths = paths
    

    def exists(self) -> bool:
        return os.path.exists(str(self))
    

    def file(self, mode: _OPEN_TEXT_MODE="r", non_existent_ok: bool=False) -> typing.TextIO:
        if not self.exists() and not non_existent_ok:
            raise FileNotFoundError(parse_message(FILE_NOT_FOUND, PATH=str(self)))
        elif not os.path.isfile(str(self)):
            raise NotADirectoryError(parse_message(NOT_FILE, PATH=str(self)))
        
        file = open(str(self), mode)

        return file
    

    def items(self) -> list["Path"]:
        if not os.path.isdir(self._path):
            raise NotADirectoryError(parse_message(NOT_DIRECTORY, PATH=self))
        
        items_name = os.listdir(self._path)
        items = []
        for item_name in items_name:
            item = Path(str(self), item_name)
            items.append(item)

        return items
    

    def mkdir(self, exists_ok: bool=False):
        if os.path.exists(str(self)):
            if exists_ok:
                return
            raise FileExistsError(parse_message(DIRECTORY_ALREADY_EXISTS, PATH=str(self)))
        
        path = ""
        for p in self._paths:
            path = os.path.join(path, p)

            os.makedirs(path, exist_ok=exists_ok)
        

    def get_not_existent_name(self, *paths) -> "Path":
        paths = [str(self)] + Path._parse_path(paths)
        path = os.path.join(*paths)

        while os.path.exists(path):
            path = gen_anonymous_name(path, False, 5)

        return Path(path)


    def __str__(self) -> str:
        return os.path.join(*self._paths)
    

    def __repr__(self) -> typing.Literal['<Path: "<path>">']:
        return f"<Path: {str(self)}>"