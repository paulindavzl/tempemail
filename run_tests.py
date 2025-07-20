import pytest

from tempemail.core.messeger import TESTS_INTERRUPTED, TESTS_PATH

def run():
    try:
        pytest.main([TESTS_PATH, "-vv"])
    except KeyboardInterrupt:
        print(TESTS_INTERRUPTED)