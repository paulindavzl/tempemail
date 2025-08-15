class PathNotFoundException(Exception):
    """arquivo não encontrado"""


class InvalidEmailException(Exception):
    """e-mail inválido"""


class InvalidContentException(Exception):
    """conteúdo inválido"""


class EnvironmentVariableRequiredException(Exception):
    """variável de ambiente obrigatória ausente"""


class EmptyEnvfileException(Exception):
    """parâmetro envfile vazio (None)"""


class NotFileException(Exception):
    """o caminho não leva à um arquivo"""


class NotDirectoryException(Exception):
    """o caminho não leva à um diretório"""


class PathExistsException(Exception):
    """o caminho já existe"""