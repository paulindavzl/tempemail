import os
import re
import json
import typing
import hashlib
import mimetypes
import jsonschema

from ..models.email_data import Email
from ..exceptions import *
from .messeger import (
    FILE_NOT_FOUND,
    NOT_DIRECTORY,
    NOT_FILE,
    DIRECTORY_ALREADY_EXISTS,
    INVALID_EMAIL,
    _METADATA_SCHEME_JSON
)


_OPEN_TEXT_MODE: typing.TypeAlias = typing.Literal['r', 'rb', 'r+', 'rb+', 'w', 'wb', 'w+', 'wb+', 'a', 'ab', 'a+', 'ab+', 'x', 'xb', 'x+', 'xb+']
METADATA: typing.TypeAlias =  dict[typing.Literal[
    "subject", "sender", "destination", "date", "rid", "content_length", "extension", "hash", "attachments",
], str|int]


def parse_message(message: str, **replace: str) -> str:
    """
    (USO INTERNO) modifica mensagens especiais, trocando TAGS por palavras/frases.

    ### parâmetros:

        message (str): mensagem especial contendo <TAGS>
        **replace (dict[str, str]): nome das <TAGS> e suas substituições

    ### uso:

        from tempemail.core.messeger import FILE_NOT_FOUND

        print(FILE_NOT_FOUND) # "the file <PATH> was not found!"

        parsed_message(FILE_NOT_FOUND, PATH="./file.txt")
        print(parsed_message) # "the file ./file.txt was not found!"
    """
    if not "<" in message or not ">" in message:
        raise 
    for tag, value in replace.items():
        message = message.replace(f"<{tag}>", str(value))

    return message


def get_email_hash(email: "Email") -> str:
    """
    USO INTERNO
    """
    sha = hashlib.sha256(str("".join([
        email.subject.strip().lower(),
        email.content.strip().lower(),
        email.sender.strip().lower(),
        str(email.destination).strip().lower(),
        email.date.strip().lower()
    ])).encode()).hexdigest()

    return sha


def get_email_from(path: "Path") -> "Email":
    """
    obtém um e-mail salvo em em memória.

    ### parâmetros:

        path (Path): instância da classe Path, representando o caminho para o e-mail

    ### uso:

        path = Path(".", "project_name", "emails", "email_subject_name_0")

        email = get_email_from(path)

        print(email.subject) # "email subject name"
        print(email.sender) # "sender@exemplo.com"
    """
    if not path.exists:
        raise FileNotFoundException(parse_message(FILE_NOT_FOUND, PATH=str(path)))
    elif not is_valid_email_in(path):
        raise InvalidEmailException(parse_message(INVALID_EMAIL, PATH=str(path)))
        
    meta_path = path.join("metadata.json")
    metadata: METADATA
    with meta_path.file() as meta:
        metadata = json.load(meta)

    content_path = path.join("content" + metadata["extension"])
    content: str
    with content_path.file() as content_file:
        content = content_file.read()

    attachments: dict[str, dict[typing.Literal["content_type", "payload", "main_type", "sub_type"], str]] = {}
    att_paths = path.items(ignore=[meta_path.name, content_path.name])
    for att_path in att_paths:
        mime_type, _ = mimetypes.guess_type(str(att_path))
        mime_type = mime_type or "application/octet-stream"
        main_type, sub_type = mime_type.split("/")
        content_type, _ = mimetypes.guess_type(str(att_path))

        with att_path.file("rb") as attachment:
            attachments[att_path.name] = {
                "content_type": content_type,
                "payload": attachment.read(),
                "main_type": main_type,
                "sub_type": sub_type
            }

    email = Email(
        destination=metadata["destination"],
        sender=metadata["sender"],
        subject=metadata["subject"],
        content=content,
        date=metadata["date"],
        attachments=attachments
    )

    return email


def is_valid_email_in(path: "Path") -> bool:
    """
    verifica se o e-mail salvo no caminho infomado é válido, com base nos metadados.

    ### parâmetros:

        path (Path): instância da classe Path, representando o caminho para o e-mail salvo

    ### uso:

        path = Path(".", "project_name", "emails")

        email_path =  path.join("email_subject_name_0")

        if is_valid_email_in(email_path):
            email = get_email_from(email_path) # agrupa as informações do e-mail

            print(f'o e-mail salvo em "{str(email_path)}", com o assunto: "{email.subject}", é válido!') 
            # 'o e-mail salvo em "./project_name/emails/email_subject_name_0/", com o assunto: "email subject name", é válido!'
        else:
            print(f'o e-mail salvo em "{str(email_path)}" é inválido!') 
            # 'o e-mail salvo em "./project_name/emails/email_subject_name_0/" é inválido'
    """

    if not path.exists:
        raise FileNotFoundException(parse_message(FILE_NOT_FOUND, PATH=str(path)))
    
    meta = path.join("metadata.json")
    metadata: dict
    with meta.file() as metafile:
        metadata = json.load(metafile)

    try:
        jsonschema.validate(metadata, _METADATA_SCHEME_JSON)
    except jsonschema.ValidationError:
        return False
    
    attachments: list[dict[str, str]] = metadata.get("attachments")
    if attachments:
        for att in attachments:
            name = att["name"]
            att_path = path.join(name)
            
            if not os.path.exists(att_path):
                return False
            
            with att_path.file("rb") as file:
                if not hashlib.sha256(file.read()) == att["hash"]:
                    return False
    
    extension: str = metadata["extension"]

    content_path = path.join("content" + extension)
    content: str = content_path.file()

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

        @property
        def exists(self) -> bool: verifica se o caminho representado existe

        def parser(self, in_self: bool=False, full: bool=True) -> None|Path: remove caractéres dos nomes dos componentes que possam causar problemas

        def file(self, mode: _OPEN_TEXT_MODE="r", non_existent_ok: bool=False) -> TextIO: abre um arquivo e retorna-o, possibilitando manipulação

        @property
        def items(self) -> list[Path]: retorna todos os componentes do diretório do caminho representado e retorna-os representados em uma instância de Path

        def mkdir(self, exists_ok: bool=False): cria todos os arquivos do caminho representado caso não existam

        def get_non_existent_name(self, *paths) -> Path: adiciona um componente ao caminho representado com um nome novo, evitando conflitos com arquivos já existentes.

        @property
        def name(self) -> str: retorna o nome do diretório ou arquivo representado

    ### uso:

        path = Path(".", "project_name", "directory")

        print(path) # "./project_name/directory/"

        print(path.exists) # True | False

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
        paths = list(paths) if isinstance(paths, (tuple, list)) else [paths]
        return paths
    

    @typing.overload
    def parser(self, /, full: bool=True) -> "Path": ...

    @typing.overload
    def parser(self, in_self: bool, full: bool=True) -> typing.Optional["Path"]: ...

    def parser(self, in_self: bool=False, full: bool=True) -> typing.Optional["Path"]:
        """
        remove caractéres dos nomes dos componentes que possam causar problemas.

        ### parâmetros:

            in_self (bool): define se será retornado uma nova instância de Path ou se a mudânça ocorrerá na mesma instância
            full (bool): define se todos os componentes serão modificados ou somente o último

        ### uso:

            path = Path(".", "project name", "filename to example.txt")
            print(path) # "./project name/filename to example.txt"

            new_path = path.parser(full=True) # altera todos os componentes e retorna uma nova instância
            print(new_path) # "./project_name/filename_to_example.txt"

            path.parser(in_self=True, full=False) # altera somente o último componente da mesma instância
            print(path) # "./project name/filename_to_example.txt"
        """
        components = self._paths if full else [self._paths[-1]]

        new_components = []
        for comp in components:
            comp = re.sub(
                r"[^\w\-_\.]",
                "_",
                comp
            )

            new_components.append(comp)

        new_paths = new_components if full else self._paths[:-1] + new_components

        if not in_self:
            return Path(*new_paths)
        
        self._paths = new_paths


    @typing.overload
    def join(self, /, *paths: str) -> "Path": ...

    @typing.overload
    def join(self, in_self: bool, *paths: str) -> "Path": ...

    def join(self, *paths: str, **param: bool) -> "Path":
        """
        adiciona um componente ao caminho já representado

        ### parâmetros:

            paths (tuple[str]): nomes dos componentes que serão adicionados no caminho já salvo
            in_self (bool): define se os componentes serão adicionados na mesma classe ou gerarão um classe nova

        ### uso:

            path = Path(".", "project_name", "directory")

            path.join("subdirectory", in_self=True) # adiciona outro componente na mesma classe
            print(path) # "./project_name/directory/subdirectory/"

            file = path.join("file.txt") # adiciona outro componente e retorna um nova classe
            print(file) # "./project_name/directory/subdirectory/file.txt"

        """
        paths = [str(self)] + Path._parse_path(paths)
        if not param.get("in_self", False):
            path = Path(*paths)
            return path
        
        self._paths = paths
    

    @property
    def exists(self) -> bool:
        """
        verifica se o caminho representado existe.

        ###  uso:

            path = Path(".", "project_name", "directory", "file.txt")

            if path.exists:
                print(f'o arquivo "{path.name}" ({str(path)}) existe!') # o arquivo "file.txt" (./project_name/directory/) existe!
            else:
                print(f'o arquivo "{path.name}" ({str(path)}) não existe!') # o arquivo "file.txt" (./project_name/directory/) existe!
        """
        return os.path.exists(str(self))
    

    def file(self, mode: _OPEN_TEXT_MODE="r", non_existent_ok: bool=False) -> typing.TextIO:
        """
        abre um arquivo e retorna-o, possibilitando manipulação.

        ### parâmetros:

            mode (_OPEN_TEXT_MODE): modo de abertura do arquivo ("r", "w", "a", ...)
            non_existent_ok (bool): quando False, gera um erro caso o arquivo não exista

        ### uso:

            path = Path(".", "project_name", "directory", "file.txt")

            with path.file("w") as file:
                file.write("exemplo")
        """
        if not self.exists and not non_existent_ok:
            raise FileNotFoundException(parse_message(FILE_NOT_FOUND, PATH=str(self)))
        elif not os.path.isfile(str(self)):
            raise NotADirectoryError(parse_message(NOT_FILE, PATH=str(self)))
        
        file = open(str(self), mode)

        return file
    

    @typing.overload
    def items(self, /) -> list["Path"]: ...
    
    @typing.overload
    def items(self, ignore: list[str]) -> list["Path"]: ...
    
    def items(self, ignore: list[str]=None) -> list["Path"]:
        """
        retorna todos os componentes do diretório do caminho representado e retorna-os representados em uma instância de Path.

        ### uso:

            '''
            exemplo de estrutura:

            user/
                project_name/
                    directory/
                        file1.txt
                        file2.txt
                        ...
            '''

            path = Path(".", "project_name", "directory")

            files = path.items()
            print(files) # ['<Path: "./project_name/directory/file1.txt">''<Path: "./project_name/directory/file2.txt">', ...]

            for file in files:
                print(file.name) # "file1.txt" / "file2.txt"
        """
        if not os.path.isdir(str(self)):
            raise NotADirectoryError(parse_message(NOT_DIRECTORY, PATH=self))
        
        items_name = os.listdir(self._path)
        items = []
        for item_name in items_name:
            if ignore and item_name in ignore:
                continue
                
            item = Path(str(self), item_name)
            items.append(item)

        return items
    

    def mkdir(self, exists_ok: bool=False):
        """
        cria todos os arquivos caso não existam.

        ### parâmetros:

            exists_ok (bool): quando False, gera um erro se o diretório já existir

        ### uso:

            '''
            exemplo de estrutura (antes de Path.mkdir(...)):

            user/
            '''

            path = Path(".", "project_name", "directory")
            
            if not path.exists: # False
                path.mkdir(exists_ok=True)

            '''
            exemplo de estrutura (depois de Path.mkdir(...)):

            user/
                project_name/
                    directory/
            '''
        """
        if os.path.exists(str(self)):
            if exists_ok:
                return
            raise FileExistsError(parse_message(DIRECTORY_ALREADY_EXISTS, PATH=str(self)))
        
        path = ""
        for p in self._paths:
            path = os.path.join(path, p)

            os.makedirs(path, exist_ok=exists_ok)
        

    def get_non_existent_name(self, *paths) -> "Path":
        """
        adiciona um componente ao caminho representado com um nome novo, evitando conflitos com arquivos já existentes.

        ### parâmetros:

            paths (tuple[str]): nomes dos componentes que serão adicionados no caminho já salvo

        ### uso:

            path = Path(".", "project_name", "directory")

            file1 = path.join("file.txt") # adiciona outro componente no caminho
            print(file1) # "./project_name/directory/file.txt"

            file2 = path.get_non_existent_name("file.txt",) # adiciona outro componente com o mesmo nome de um componente já existente
            print(file2) # "./project_name/directory/file_0.txt"
        """
        paths = [str(self)] + Path._parse_path(paths)
        path = os.path.join(*paths)

        ext = ""
        if not os.path.isdir(path):
            points = path.split(".")
            ext = "." + points[-1]

            path = path.replace(ext, "")

        rounder = 0
        while os.path.exists(path + ext if ext else ""):
            path += f"_{rounder}"

            rounder += 1

        return Path(path + ext if ext else "")
    

    @property
    def name(self) -> str:
        """
        retorna o nome do diretório ou arquivo representado

        ### uso:

            path = Path(".", "project_name", "directory")
            
            print(path) # "directory"
        """
        return self._paths[-1]


    def __str__(self) -> str:
        return os.path.join(*self._paths)
    

    def __repr__(self) -> typing.Literal['<Path: "<path>">']:
        return f'<Path: "{str(self)}">'