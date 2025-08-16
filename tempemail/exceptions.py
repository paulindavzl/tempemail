class TempEmailBaseExceptions(BaseException):
    '''base para todas as exceções da biblioteca "tempemail"'''


class PathNotFoundException(TempEmailBaseExceptions):
    """caminho não encontrado"""


class InvalidEmailException(TempEmailBaseExceptions):
    """e-mail inválido"""


class InvalidContentException(TempEmailBaseExceptions):
    """conteúdo inválido"""


class EnvironmentVariableRequiredException(TempEmailBaseExceptions):
    """variável de ambiente obrigatória ausente"""


class EmptyEnvfileException(TempEmailBaseExceptions):
    """parâmetro envfile vazio (None)"""


class NotFileException(TempEmailBaseExceptions):
    """o caminho não leva à um arquivo"""


class NotDirectoryException(TempEmailBaseExceptions):
    """o caminho não leva à um diretório"""


class PathExistsException(TempEmailBaseExceptions):
    """o caminho já existe"""


class ReceiverOFFException(TempEmailBaseExceptions):
    """receptor de e-mails desativado"""


class TimeoutException(TempEmailBaseExceptions):
    """tempo de espera expirado"""


class UnexpectedTypeException(TempEmailBaseExceptions):
    """tipo do valor inesperado em um parâmetro"""


class UnexpectedValueException(TempEmailBaseExceptions):
    """valor de um parâmetro inesperado"""