import os
import re
from io import TextIOWrapper

from tempemail.core.utils import *
from tempemail.core.messeger import PATH_NOT_FOUND

from tests_tempemail.conftest import compare, create_structure_path


def test__parse_message():
    assert PATH_NOT_FOUND == "the <TYPE> <PATH> was not found! <COMPLEMENT>"

    assert parse_message(PATH_NOT_FOUND, PATH="./file.txt", TYPE="file") == "the file ./file.txt was not found!"
    assert parse_message(PATH_NOT_FOUND, PATH="./file.txt", TYPE="directory") == "the directory ./file.txt was not found!"


def test__path():
    path = Path(".", "test", "testing")

    _path = os.path.join(".", "test", "testing")

    assert compare(path, _path)
    assert re.escape(repr(path)) == re.escape(f'<Path: "{_path}">')

    assert path.name == "testing"
    assert path.exists == os.path.exists(_path)


def test__path__parser():
    path = Path(".", "test", "tes tin@", "t esting2()")

    unparsed = os.path.join(".", "test", "tes tin@", "t esting2()")
    full_parsed = os.path.join(".", "test", "tes_tin_", "t_esting2__")
    end_parsed = os.path.join(".", "test", "tes tin@", "t_esting2__")

    assert compare(path, unparsed)

    assert compare(path.parser(full=True), full_parsed)
    assert compare(path.parser(full=False), end_parsed)

    assert compare(path, unparsed)

    path.parser(in_self=True, full=False)
    assert compare(path, end_parsed)

    path.parser(in_self=True, full=True)
    assert compare(path, full_parsed)


def test__path__join():
    path = Path(".", "project_name")

    default_path = os.path.join(".", "project_name")
    joined_path = os.path.join(default_path, "join")

    assert compare(path, default_path)

    new_path_joinend = path.join("join")
    assert compare(new_path_joinend, joined_path)

    assert not compare(path, joined_path)
    assert compare(path, default_path)

    path.join("join", in_self=True)

    assert compare(path, joined_path)
    assert not compare(path, default_path)


def test__path__exists():
    tests_path = Path(".", "tests_tempemail")
    assert tests_path.exists

    conftest_path = tests_path.join("conftest.py")
    assert conftest_path.exists

    non_existent_path = tests_path.join("non_existent_path.txt")
    assert not non_existent_path.exists 


def test__path__file(data_to_tests: Path):
    data_to_tests.mkdir(True)
    assert data_to_tests.exists

    path = data_to_tests.join("test_file.txt")

    assert not path.exists

    with path.file(mode="w", non_existent_ok=True) as file:
        assert type(file) == TextIOWrapper
        assert file.mode == "w"
        assert compare(path, file.name)

    assert path.exists


def test__path__items(data_to_tests: Path):
    items = {
        "directory1": "directory",
        "directory2": "directory",
        "file1": "file",
        "file2": "file"
    }

    assert not data_to_tests.exists

    create_structure_path(data_to_tests)

    assert data_to_tests.exists

    main = data_to_tests.join("example_structure_path")

    for item in main.items():
        typ = items.get(item.name)

        assert item.is_type(typ)


def test__path__mkdir(data_to_tests: Path):
    directory = data_to_tests.join("directory")
    subdirectory = directory.join("subdirectory")

    assert not directory.exists
    assert not subdirectory.exists

    subdirectory.mkdir(exists_ok=True)

    assert directory.exists
    assert subdirectory.exists


def test__path__free_name(data_to_tests: Path):
    path_directory = data_to_tests.join("directory")
    path_directory.mkdir(True)

    free_name_directory = data_to_tests.free_name("directory")

    assert free_name_directory.name == "directory_2"

    path_file = data_to_tests.join("file.txt")
    path_file.file(mode="w", non_existent_ok=True).close()

    free_name_file = data_to_tests.free_name("file.txt")

    assert free_name_file.name == "file_2.txt"


def test__path__is_type(data_to_tests: Path):
    directory = data_to_tests.join("directory")
    directory.mkdir(True)

    file = data_to_tests.join("file.txt")
    file.file("w", True).close()

    assert directory.exists
    assert file.exists

    assert directory.is_type() == "directory"
    assert file.is_type() == "file"

    assert directory.is_type("directory")
    assert file.is_type("file")


def test__path__remove__without__ignore(data_to_tests: Path):
    root = data_to_tests.join("root")

    create_structure_path(root)

    assert root.exists

    root.remove(non_existent_ok=True)

    assert not root.exists


def test__path__remove__with__ignore(data_to_tests: Path):
    root = data_to_tests.join("root")
    ignore = [
        ("root", "example_structure_path", "directory1"),
        ("root", "example_structure_path", "file2.txt")
    ]

    create_structure_path(root)

    assert root.exists

    root.remove(True, ignore, True)

    assert root.exists
    for comp in root.items():
        assert comp.name == "example_structure_path"

        for item in comp.items():
            assert item.name in ["directory1", "file2.txt"]


def test__path__name(data_to_tests: Path):
    assert data_to_tests.name == "data_to_tests"
