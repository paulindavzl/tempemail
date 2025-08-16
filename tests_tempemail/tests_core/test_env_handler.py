import pytest

from tempemail import EnvHandler, Path

from tests_tempemail.conftest import configure_env


def gen_env(test_env: Path):
    with test_env.file("w", True) as env:
        env.write('''
SERVER='localhost',
PORT=1025,
TEST='test'
''')


@pytest.fixture
def env(test_env: Path):
    configure_env(test_env)
    _e = EnvHandler(test_env)
    _e.load()
    return _e


def test__env_handler(env: EnvHandler, test_env: Path):
    assert repr(env) == f"<EnvHandler: {test_env}>"
    assert str(env) == str(test_env)


def test__env_handler__get_all_variables(test_env: Path):
    gen_env(test_env)

    env_handler = EnvHandler(test_env)
    env_handler.get_all_variables()

    assert env_handler.TEST == "test"


def test__env_handler__load(env: EnvHandler, test_env: Path):
    assert env.SERVER == "localhost"

    env.set_env(
        reload=False,
        SERVER="test"
    )

    assert env.SERVER == "localhost"

    content: list
    with test_env.file() as file:
        content = [c.strip() for c in file.readlines()]

    assert "SERVER='test'" in content

    env.load()

    assert env.SERVER == "test"


def test__env_handler__set_env(env: EnvHandler):
    assert env.SERVER == "localhost"
    assert env.PORT == "1025"
    assert getattr(env, "TEST", None) is None

    env.set_env(
        SERVER="test_server",
        PORT="5000",
        TEST="testing"
    )

    assert env.SERVER == "test_server"
    assert env.PORT == "5000"
    assert env.TEST == "testing"


def test__env_handler__set_default(env: EnvHandler):
    assert env.SERVER == "localhost"
    assert env.PORT == "1025"

    env.set_env(
        SERVER={"value": "default_server", "rule": "common"},
        PORT={"value": "default_port", "rule": "common"},
        TEST="testing",
        setteds_ok=False
    )

    env.SERVER = "test_server"
    env.PORT = "5000"

    assert env.SERVER == "test_server"
    assert env.PORT == "5000"
    assert env.TEST == "testing"

    env.set_env(TEST="testing2")
    assert env.TEST == "testing2"

    env.set_default(exists_ok=False)

    assert env.SERVER == "default_server"
    assert env.PORT == "default_port"
    assert env.TEST == "testing"


def test__env_handler__unique(env: EnvHandler, test_env: Path, data_to_tests: Path):
    other_path = data_to_tests.join("other.env")
    gen_env(other_path)
    other_env = EnvHandler(other_path)

    assert env != other_env

    env_unique = EnvHandler.unique(test_env)
    other_env_unique = EnvHandler.unique(other_path)

    assert env == env_unique
    assert other_env == other_env_unique