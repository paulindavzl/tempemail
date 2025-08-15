import os
import re
import json
from io import TextIOWrapper

from tempemail.core.utils import *
from tempemail.core.utils import get_email_hash
from tempemail.core.messeger import PATH_NOT_FOUND
from tempemail import EmailHandler, EnvHandler, Email

from tests_tempemail.conftest import compare, create_structure_path, configure_env


def test__parse_message():
    assert PATH_NOT_FOUND == "the <TYPE> <PATH> was not found! <COMPLEMENT>"

    assert parse_message(PATH_NOT_FOUND, PATH="./file.txt", TYPE="file") == "the file ./file.txt was not found!"
    assert parse_message(PATH_NOT_FOUND, PATH="./file.txt", TYPE="directory") == "the directory ./file.txt was not found!"


def test__get_email_hash(test_env: Path, data_to_tests: Path):
    configure_env(test_env)

    emails = data_to_tests.join("emails")
    handler = EmailHandler(EnvHandler.unique(str(test_env)))
    handler.save_in(emails)

    email = Email(
        destination="dest@localhost.com",
        sender="send@localhost.com",
        subject="Test Subject",
        content="test content."
    )

    with handler:
        handler.send(email)

    metadata_path = emails.join("dest_localhost.com", "Test_Subject", "metadata.json")

    assert metadata_path.exists

    metadata: dict
    with metadata_path.file() as meta:
        metadata = json.load(meta)

    email_hash = metadata["hash"]

    assert get_email_hash(email) == email_hash

    email.content = ""
    assert get_email_hash(email) != email_hash


def test__get_email_from(test_env: Path, data_to_tests: Path):
    configure_env(test_env)

    emails = data_to_tests.join("emails")
    handler = EmailHandler(EnvHandler.unique(str(test_env)))
    handler.save_in(emails)

    email = Email(
        destination="dest@localhost.com",
        sender="send@localhost.com",
        subject="Test Subject",
        content="test content."
    )

    with handler:
        handler.send(email)

    subject_path = emails.join("dest_localhost.com", "Test_Subject")
    rec_email = get_email_from(subject_path)

    assert email.content == rec_email.content
    assert email.rid == rec_email.rid


def test__is_valid_email_in(test_env: Path, data_to_tests: Path):
    configure_env(test_env)

    emails = data_to_tests.join("emails")
    handler = EmailHandler(EnvHandler.unique(str(test_env)))
    handler.save_in(emails)

    email = Email(
        destination="dest@localhost.com",
        sender="send@localhost.com",
        subject="Test Subject",
        content="test content."
    )

    with handler:
        handler.send(email)

    subject_path = emails.join("dest_localhost.com", "Test_Subject")

    assert is_valid_email_in(subject_path)


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


def test__path__rename(data_to_tests: Path):
    root = data_to_tests.join("root")
    create_structure_path(root)

    main = root.join("example_structure_path", "file1.txt")
    assert main.exists

    main.rename("renamed.txt")

    assert main.exists
    assert main.name == "renamed.txt"


def test__path__name(data_to_tests: Path):
    assert data_to_tests.name == "data_to_tests"
