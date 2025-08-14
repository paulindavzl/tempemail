import pytest

from tempemail import EmailHandler, UserModel, Path, EnvHandler, Email, is_valid_email_in

from tests_tempemail.conftest import configure_env


@pytest.fixture
def user(env: EnvHandler) -> UserModel:
    return UserModel(env)


@pytest.fixture
def env(test_env: Path) -> EnvHandler:
    return EnvHandler.unique(str(test_env))


@pytest.fixture
def handler(env: EnvHandler) -> EmailHandler:
    configure_env(str(env))
    return EmailHandler(env)


def email(index: int=1) -> Email:
    return Email(
        destination=f"dest{index}@localhost.com",
        sender=f"send{index}@localhos.com",
        subject=f"Test Subject {index}",
        content=f"test content {index}"
    )


def test__email_handler(handler: EmailHandler, data_to_tests: Path):
    assert not handler.receiver_running
    assert repr(handler) == f"<EmailHandler receiver=off save=off extension=.txt env={str(data_to_tests.join("tests.env"))}>"


def test__email_handler__send(handler: EmailHandler):
    with handler:
        assert handler.send(email()).status == "250 FULL-SUCCESSFUL"


@pytest.mark.asyncio
async def test__email_handler__wait_emails__address_any(handler: EmailHandler):
    with handler:
        handler.send([email(1), email(2), email(3)])

        emails = handler.wait_emails(timeout=0.5, raiser=False)
        async for _email in emails:
            assert all([
                _email.destination[0] in ["dest1@localhost.com", "dest2@localhost.com", "dest3@localhost.com"],
                _email.subject in ["Test Subject 1", "Test Subject 2", "Test Subject 3"],
                _email.content in ["test content 1", "test content 2", "test content 3"]
            ])


@pytest.mark.asyncio
async def test__email_handler__wait_emails__address_specific(handler: EmailHandler):
    with handler:
        handler.send([email(1), email(2), email(3)])

        emails = handler.wait_emails(address="dest2@localhost.com", timeout=0.5, raiser=False)
        async for _email in emails:
            assert _email.destination[0] == "dest2@localhost.com"
            assert _email.subject == "Test Subject 2"
            assert _email.content == "test content 2"


@pytest.mark.asyncio
async def test__email_handler__save_in(data_to_tests: Path, handler: EmailHandler):
    path = data_to_tests.join("emails")
    assert not path.exists

    handler.save_in(path)
    assert path.exists

    mail1 = email(1)
    email1_path = path.join(str(mail1.destination))
    email1_path.parser(in_self=True)

    mail1_2 = email(1)

    mail2 = email(2)
    email2_path = path.join(str(mail1.destination))
    email2_path.parser(in_self=True)

    assert not email1_path.exists
    assert not email2_path.exists

    with handler:
        handler.send([mail1, mail1_2, mail2])

    assert email1_path.exists
    assert email2_path.exists

    assert len(email1_path.items()) == 2

    email_1_subject = email1_path.join("Test_Subject_1")
    content_path = email_1_subject.join("content.txt")

    with content_path.file() as content:
        assert content.read() == "test content 1"

    assert is_valid_email_in(email_1_subject)