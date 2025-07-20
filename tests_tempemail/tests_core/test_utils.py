import pytest

from tempemail.core.utils import *
from tempemail.core.messeger import FILE_NOT_FOUND


def test_parse_message():
    assert FILE_NOT_FOUND == "the file <PATH> was not found!"

    assert parse_message(FILE_NOT_FOUND, PATH="./file.txt") == "the file ./file.txt was not found!"


