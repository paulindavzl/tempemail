import pytest
from tempemail import Path, EnvHandler


@pytest.fixture
def test_env() -> Path:
    path = Path("tests.env")
    return path


def configure_env(test_env: Path):
    env = EnvHandler.unique(str(test_env))
    env.set_env(
        SERVER="localhost",
        PORT=1025
    )


@pytest.fixture(autouse=True)
def remove_test_env(test_env: Path):
    test_env.remove(non_existent_ok=True)
    configure_env(test_env)

    yield

    test_env.remove(non_existent_ok=True)