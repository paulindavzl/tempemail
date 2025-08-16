import pytest
from tempemail import Path, EnvHandler


def compare(param1: Path, param2: str) -> bool:
    return str(param1) == str(param2)


@pytest.fixture
def data_to_tests() -> Path:
    path = Path(".", "tests_tempemail", "data_to_tests")
    return path


def create_structure_path(path: Path):
    path.mkdir(True)
    
    main = path.join("example_structure_path")
    main.mkdir(exists_ok=True)

    directory1 = main.join("directory1")
    directory1.mkdir(exists_ok=True)

    directory2 = main.join("directory2")
    directory2.mkdir(exists_ok=True)

    file1 = main.join("file1.txt")
    file1.file("w", non_existent_ok=True).close()

    file2 = main.join("file2.txt")
    file2.file("w", non_existent_ok=True).close()


@pytest.fixture
def test_env(data_to_tests: Path) -> Path:
    data_to_tests.mkdir(True)
    
    path = data_to_tests.join("tests.env")
    return path


def configure_env(test_env: Path):
    env = EnvHandler.unique(test_env)
    env.set_env(
        SERVER="localhost",
        PORT=1025
    )


@pytest.fixture(autouse=True)
def remove_data_to_tests(data_to_tests: Path):
    data_to_tests.remove(non_existent_ok=True)

    yield

    data_to_tests.remove(non_existent_ok=True)