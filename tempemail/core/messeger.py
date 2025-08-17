WAIT_EMAIL_COOLDOWN = 0.2
OPEN_TEXT_MODE = ['r', 'rb', 'r+', 'rb+', 'w', 'wb', 'w+', 'wb+', 'a', 'ab', 'a+', 'ab+', 'x', 'xb', 'x+', 'xb+']
DEFAULT_NAME = "anonymous"
MISSING_VARIABLE = "the <NAME> variable does not exist! <COMPLEMENT>"
PATH_NOT_FOUND = "the <TYPE> <PATH> was not found! <COMPLEMENT>"
PATH_ARE_NOT_DEFINED = "the path to save emails is not defined! use EmailHandler.save_in(...) to define a path."
NOT_DIRECTORY = "the path <PATH> does not point to a directory! <COMPLEMENT>"
NOT_FILE = "the path <PATH> does not point to a file! <COMPLEMENT>"
RECEIVER_OFF = """can't <OBJECTIVE> emails with receiver turned off! Use "with EmailHandler()" or "EmailHandler.open()" to enable receiver."""
DIRECTORY_ALREADY_EXISTS= "the directory in <PATH> already exists! <COMPLEMENT>"
INVALID_EMAIL = f'the email in "<PATH>" is invalid! <COMPLEMENT>'
TESTS_INTERRUPTED = "tests interrupted by user!"
TESTS_PATH = "tests_tempemail"
EMPTY_ENVFILE = "envfile not provided (None)! Please provide an envfile."
STATUS_250 = "250 FULL-SUCCESSFUL"
STATUS_200 = "200 OK"
STATUS_500 = "500 REFUSED"
PATH_EXISTS = "A <TYPE> named <NAME> already exists! Use another name."
TIMEOUT = "the <TIME> second cooldown timed out!"
UNEXPECTED_TYPE = "<METHOD> expected an <EXPECTED> in the <PARAMETER> parameter, but received a <RECEIVED>!"
INVALID_EXTENSION = 'the extension must start with "."!'
UNEXPECTED_RULE = 'rules for environment variables must be "required" or "common"! rule: <RULE>.'
INVALID_OPEN_TEXT_MODE = f'The file open mode "<MODE>" is invalid! Use: {", ".join([f"{m}" for m in OPEN_TEXT_MODE])}.'
UNEXPECTED_EXPECTED = 'expected must be "directory" or "file"! expected: <EXPECTED>.'

_METADATA_SCHEME_JSON = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["subject", "sender", "destination", "date", "rid", "content_length", "hash", "extension"],
    "properties": {
        "subject": {"type": "string"},
        "sender": {"type": "string", "format": "email"},
        "destination": {
            "oneOf": [
                {"type": "string", "format": "email"},
                {
                    "type": "array",
                    "items": {"type": "string", "format": "email"}
                }
            ]
        },
        "date": {"type": "string"},
        "rid": {"type": "string"},
        "content_length": {"type": "integer", "minumum": 0},
        "extension": {"type": "string"},
        "hash": {"type": "string", "pattern": "^[a-fA-F0-9]{64}$"},
        "attachments": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "type", "hash"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "hash": {"type": "string", "pattern": "^[a-fA-F0-9]{64}$"}
                }
            }
        }
    },
    "additionalProperties": False
}
