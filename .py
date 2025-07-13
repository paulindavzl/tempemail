import asyncio
from tempemail import Sender, Email, EmailHandler, UserModel


email_data = Email(
    destination="dest@localhost.com",
    user=UserModel(),
    content="this a test content",
    subject="testing"
)


sender = Sender()


handler = EmailHandler()


async def wait():
    with handler:
        handler.send(email_data)

        emails = handler.wait_emails()

        async for email in emails:
            print(email.content)


asyncio.run(wait())