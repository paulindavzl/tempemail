class FileNotFoundException(Exception):
    """arquivo não encontrado"""


class InvalidEmailException(Exception):
    """e-mail inválido"""


class InvalidContentException(Exception):
    """conteúdo inválido"""


class EnvironmentVariableRequiredException(Exception):
    """variável de ambiente obrigatória ausente"""


class EmptyEnvfileException(Exception):
    """parâmetro envfile vazio (None)"""