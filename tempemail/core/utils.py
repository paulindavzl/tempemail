import os
import re
import json
import typing
import hashlib
import mimetypes
import jsonschema
from io import TextIOWrapper

from ..models.email_data import Email
from ..exceptions import *
from .messeger import (
    PATH_NOT_FOUND,
    NOT_DIRECTORY,
    NOT_FILE,
    DIRECTORY_ALREADY_EXISTS,
    INVALID_EMAIL,
    _METADATA_SCHEME_JSON,
    PATH_EXISTS
)


_OPEN_TEXT_MODE: typing.TypeAlias = typing.Literal['r', 'rb', 'r+', 'rb+', 'w', 'wb', 'w+', 'wb+', 'a', 'ab', 'a+', 'ab+', 'x', 'xb', 'x+', 'xb+']
METADATA: typing.TypeAlias =  dict[typing.Literal[
    "subject", "sender", "destination", "date", "rid", "content_length", "extension", "hash", "attachments",
], str|int]


__all__ = [
    "Path",
    "is_valid_email_in",
    "parse_message",
    "get_email_from",
]

def parse_message(message: str, complement: typing.Optional[str]=None, **replace: str) -> str:
    """
    (USO INTERNO) modifica mensagens especiais, trocando TAGS por palavras/frases.

    ### parâmetros:

        message (str): mensagem especial contendo <TAGS>
        complement (Optional[str]): complemento da mensagem
        **replace (dict[str, str]): nome das <TAGS> e suas substituições

    ### uso:

        from tempemail.core.messeger import PATH_NOT_FOUND

        print(PATH_NOT_FOUND) # "the <TYPE> <PATH> was not found! <COMPLEMENT>"

        parsed_message(PATH_NOT_FOUND, PATH="./file.txt", TYPE="file")
        print(parsed_message) # "the file ./file.txt was not found!"
    """
    if not "<" in message or not ">" in message:
        raise 
    for tag, value in replace.items():
        message = message.replace(f"<{tag}>", str(value))

    complement = "" if complement is None else complement
    message = message.replace(" <COMPLEMENT>", complement)

    return message


def get_email_hash(email: "Email") -> str:
    """
    USO INTERNO
    """
    content = [
        str(email.subject).strip().lower(),
        str(email.content).strip().lower(),
        str(email.sender).strip().lower(),
        str(email.destination if isinstance(email.destination, list) else [email.destination]).strip().lower(),
    ]

    if email.date:
        content.append(str(email.date).strip().lower())
    sha = hashlib.sha256(str("".join(content)).encode()).hexdigest()

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
        raise PathNotFoundException(parse_message(PATH_NOT_FOUND, PATH=str(path), TYPE="email"))
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
        raise PathNotFoundException(parse_message(PATH_NOT_FOUND, PATH=str(path), TYPE="email"))
    
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
    content: str
    with content_path.file() as content_file:
        content = content_file.read()

    content_hash = [
        str(metadata.get("subject", "")).strip().lower(),
        content.strip().lower(),
        str(metadata.get("sender", "")).strip().lower(),
        str(metadata.get("destination", "")).strip().lower()
    ]

    if metadata.get("date"):
        content_hash.append(str(metadata["date"]).strip().lower())

    sha = hashlib.sha256(str("".join(content_hash)).encode()).hexdigest()

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

        def remove(self, non_existent_ok: bool=False, ignore: typing.Optional[list[tuple[str]]]=None): apaga o componente representado (arquivo ou diretório)

        def free_name(self, *paths) -> Path: adiciona um componente ao caminho representado com um nome novo, evitando conflitos com arquivos já existentes.

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
    def parser(self, in_self: bool, full: bool=True) -> None: ...

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
                r"[^\w\-_/\\.]",
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
    

    def file(self, mode: _OPEN_TEXT_MODE="r", non_existent_ok: bool=False) -> TextIOWrapper:
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
        if not self.exists:
            if not non_existent_ok:
                raise PathNotFoundException(parse_message(PATH_NOT_FOUND, PATH=str(self), TYPE="file"))
        elif not os.path.isfile(str(self)):
            raise NotADirectoryError(parse_message(NOT_FILE, PATH=str(self)))
        
        return open(str(self), mode)
    

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
        if not self.exists:
            raise PathNotFoundException(parse_message(PATH_NOT_FOUND, PATH=self, TYPE="directory"))
        elif not self.is_type("directory"):
            raise NotADirectoryError(parse_message(NOT_DIRECTORY, PATH=self))
        
        items_name = os.listdir(str(self))
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
        

    @typing.overload
    def free_name(self, /, *paths) -> "Path": ...

    @typing.overload
    def free_name(self, parser: bool, *paths) -> "Path": ...

    def free_name(self, *paths, **kwargs) -> "Path":
        """
        adiciona um componente ao caminho representado com um nome novo, evitando conflitos com arquivos já existentes.

        ### parâmetros:

            parser (bool): remove caractéres do nome dos componentes que possa causar problemas
            paths (tuple[str]): nomes dos componentes que serão adicionados no caminho já salvo

        ### uso:

            path = Path(".", "project_name", "directory")

            file1 = path.join("file.txt") # adiciona outro componente no caminho
            print(file1) # "./project_name/directory/file.txt"

            file2 = path.free_name("file.txt",) # adiciona outro componente com o mesmo nome de um componente já existente
            print(file2) # "./project_name/directory/file_0.txt"
        """
        paths = [str(self)] + Path._parse_path(paths)
        path = Path(*paths)

        parser = kwargs.get("parser", False)
        if parser:
            path.parser(in_self=True, full=False)

        if path.exists:
            ext = ""
            if path.is_type("file"):
                if "." in path.name:
                    ext = "." + path.name.split(".")[-1]
            
            counter = 2
            name = path.name[:-len(ext)] if ext else path.name
            while path.exists:
                name += f"_{counter}"

                path._paths[-1] = name + ext
                path.parser(in_self=True, full=False)
            
            return path

        return path
    

    @typing.overload
    def is_type(self, /) -> typing.Literal["directory", "file"]: ...

    @typing.overload
    def is_type(self, expected: typing.Literal["directory", "file"]) -> bool: ...

    def is_type(self, expected: typing.Literal["directory", "file"]=None) -> bool|typing.Literal["directory", "file"]:
        if not self.exists:
            if expected is None:
                raise PathNotFoundException(parse_message(PATH_NOT_FOUND, PATH=str(self), TYPE="path"))
            return False
        typ = "directory" if os.path.isdir(str(self)) else "file"
            
        return typ == expected if expected else typ

    
    @typing.overload
    def remove(self, non_existent_ok: bool, /): ...

    @typing.overload
    def remove(self, non_existent_ok: bool, ignore: typing.Optional[list[str]]): ...

    def remove(self, non_existent_ok: bool=False, ignore: typing.Optional[list[tuple[str]]]=None, x=None):
        """
        apaga o componente representado (arquivo ou diretório).

        ### parâmetros:

            non_existent_ok (bool): quando False, caso o componente não exista gera um erro (PathNotFoundException)
            ignore (list[str]): caminho dos componentes que devem ser ignorados. caso um diretório seja ignorado, todos seus componentes também serão

        ### uso:

            '''
            exemplo de estrutura de arquivos antes de Path.remove(...):

            ./
                project_name/
                    directory/
                        directory_file.txt
                        sub_directory_1/
                            sub_directory_1_file_1.txt
                            sub_directory_1_file_2.txt
                        sub_directory_2/
                            sub_directory_2_file_1.txt
                            sub_directory_2_file_2.txt
            '''

            path = Path(".", "project_name", "directory")

            path.remove(
                non_existent_ok=True,
                ignore=[("sub_directory_1", "sub_directory_1_file_2.txt")]
            )

            '''
            exemplo de estrutura de arquivos antes de Path.remove(...):

            ./
                project_name/
                    directory/
                        sub_directory_1/
                            sub_directory_1_file_2.txt
            '''

        ### observação:

            - caso use ignore, automaticamente o diretório que armazena o componente ignorado também será ignorado!
        """
        if not self.exists and not non_existent_ok:
            raise PathNotFoundException(parse_message(PATH_NOT_FOUND, PATH=self, TYPE="path"))
        elif ignore and self.is_type("file"):
            raise NotDirectoryException(parse_message(NOT_DIRECTORY, complement="use ignore only when removing directories.", PATH=self))
        
        ignore_parsed = [
            os.path.join(*comps) if isinstance(comps, (tuple, list)) else comps for comps in ignore
        ] if ignore else []

        def _relative_name(path: Path) -> str:
            return str(path).replace(str(self), self.name)
        
        def _ignore_item(path: Path) -> bool:
            if _relative_name(path) in ignore_parsed:
                ignore_parsed.append(self.name) if self.name not in ignore_parsed else None
                return True
            return False
                
        def _remover(path: Path, base: typing.Optional[str]=None):            
            if path.is_type("directory"):
                if _ignore_item(path):
                    if base:
                        ignore_parsed.append(base)
                
                for item in path.items():
                    _remover(item, _relative_name(path))

                if path.exists and not _ignore_item(path):
                    os.removedirs(str(path))

            else:
                if path.exists:
                    os.remove(str(path))

        _remover(self)


    def rename(self, new_name: str):
        """
        renomeia o componente representado

        ### parâmetros:

            new_name (str): novo nome do componente (arquivo/diretório)

        ### uso:

            ''' exemplo de estrutura antes de Path.rename
            ./
                project_name/
                    directory/
                        directory_file.txt
            '''

            path = Path(".", "project_name", "directory", "directory_file.txt")

            path.rename(new_name="file.txt")

            ''' exemplo de estrutura depois de Path.rename
            ./
                project_name/
                    directory/
                        file.txt
            '''
        """
        if not self.exists:
            raise PathNotFoundException(parse_message(PATH_NOT_FOUND, TYPE="path", PATH=str(self)))
        
        new_path = Path(*self._paths)
        new_path._paths[-1] = new_name
        
        if new_path.exists:
            typ = new_path.is_type()
            raise PathExistsException(parse_message(PATH_EXISTS, TYPE=typ, NAME=new_name))
        
        os.rename(str(self), str(new_path))

        self._paths = new_path._paths


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
    

class Report:
    def __init__(self, status: str, error: list[Email]=[]):
        self.status = status
        self.error = error

    
    def __str__(self):
        return self.status
    

    def __len__(self) -> int:
        return len(self.error)