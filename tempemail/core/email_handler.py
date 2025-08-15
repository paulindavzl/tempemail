"""
agrupa classes responsáveis por manipular o envio e recebimento de e-mails.
"""

import json
import asyncio
import hashlib
import smtplib
import mimetypes
import email as _email
from aiosmtpd.smtp import Envelope
from email.message import EmailMessage
from aiosmtpd.controller import Controller
from email.utils import formatdate
from typing import Optional, overload, AsyncGenerator, Literal

from .env_handler import EnvHandler
from ..models.email_data import Email
from ..exceptions import *
from .utils import (
    Path,
    Report,
    parse_message, 
    get_email_hash,
)
from .messeger import (
    WAIT_EMAIL_COOLDOWN,
    RECEIVER_OFF,
    PATH_ARE_NOT_DEFINED,
    PATH_NOT_FOUND,
    STATUS_250,
    STATUS_200,
    STATUS_500
)


class _Handler:
    __slots__ = ["emails", "handler"]

    emails: list[Email]
    handler: "EmailHandler"

    def __init__(self, handler: "EmailHandler"):
        self.emails = []
        self.handler = handler


    async def handle_DATA(self, server, session, envelope: Envelope):
        content = _email.message_from_bytes(envelope.content)
        receiver = Email(
            sender=envelope.mail_from, 
            destination=envelope.rcpt_tos,
            date=content["Date"]
        )
        receiver.subject = content["Subject"].strip()

        if content.is_multipart():
            for part in content.walk():
                filename = part.get_filename()
                content_type = part.get_content_type()
                payload = part.get_payload(decode=True)

                if filename:
                    receiver.attachments[filename] = {
                        "content_type": content_type,
                        "main_type": part.get_content_maintype(),
                        "sub_type": part.get_content_subtype(),
                        "payload": payload
                    }

                elif content_type == "text/plain":
                    receiver.content = payload.decode()
        else:
            payload = content.get_payload(decode=True)
            receiver.content = payload.decode().strip()

        self.emails.append(receiver)
        if self.handler.path is not None:
            self._save(receiver)

        return "250 OK"
    

    def _save(self, email: Email):
        if not self.handler.path:
            raise ValueError(PATH_ARE_NOT_DEFINED)
                
        self.handler.path.mkdir(True)

        email_path = self.handler.path.join("".join(email.destination))
        email_path.parser(in_self=True, full=False)
        email_path.mkdir(True)

        subject_path = email_path.free_name(email.subject, parser=True)
        subject_path.mkdir(True)

        content_path = subject_path.join("content" + self.handler.extension)
        with content_path.file("w", True) as content_file:
            content_file.write(email.content)

        metadata = {
            "subject": email.subject,
            "sender": email.sender,
            "destination": email.destination,
            "date": email.date,
            "rid": email.rid,
            "content_length": len(email.content.strip()),
            "extension": self.handler.extension,
            "hash": get_email_hash(email)
        }

        if email.attachments:
            meta_att = []
            for att_name, data in email.attachments.items():
                ext = mimetypes.guess_extension(data["content_type"]) or ".bin"
                att_name += ext

                att_path = subject_path.free_name(att_name)
                with att_path.file("wb", True) as att_file:
                    att_file.write(data["payload"])

                meta_att.append({
                    "name": att_name,
                    "type": data["content_type"],
                    "hash": hashlib.sha256(data["payload"]).hexdigest()
                })

            metadata["attachments"] = meta_att

        metadata_path = subject_path.join("metadata.json")
        with metadata_path.file("w", True) as metadata_file:
            json.dump(
                metadata, 
                fp=metadata_file, 
                indent=4,
                ensure_ascii=False
            )


class EmailHandler:
    """
    manipula o envio, recebimento e salvamento de e-mails.
    
    ### métodos:

        receiver_running (bool): retorna um booleano que indica se o receptor está ativo ou não

        def wait_emails(self, address: Optional[str]=None, repeat: Optional[int]=None, timeout: Optional[float]=None, raiser: bool=True) -> AsyncGenerator[Email]: aguarda e-mails e retorna-os, podendo filtrá-los baseado em um endereço de e-mail específico

    ### uso básico:

        para receber e-mails, você deve iniciar um gerenciador de contexto e iterar de forma assíncrona sobre a o método `wait_emails`:

            handler = EmailHandler(env_handler)

            with handler:
                
                emails = handler.wait_emails(...)

                async for email in emails:
                    print(f"de: {email.sender} | para: {email.destination}") # de: sender@example.com | para: [destination@example.com]
        
    """
    __slots__ = ["_handler", "_controller", "path", "extension", "_receiver_running", "_env"]

    _handler: _Handler
    _controller: Controller
    _receiver_running: bool
    path: Optional[Path]
    extension: Optional[str]
    _env: EnvHandler


    def __init__(self, env: EnvHandler):
        """
        manipula o envio, recebimento e salvamento de e-mails.

        ### parâmetros:

            env (EnvHandler): instância do manipulador de variáveis de ambiente
        """  
        self.path = None
        self._handler = _Handler(self)
        self._controller = Controller(self._handler, env.SERVER, env.PORT)
        self._receiver_running = False
        self.extension = ".txt"
        self._env = env


    @property
    def receiver_running(self) -> bool:
        """
        retorna um booleano indicando se o receptor está ativo ou não.
        """
        return self._receiver_running


    async def _get_emails(self, rids: list[str], timeout: Optional[float]=None, raiser: bool=True) -> None|list[Email]:
        if not self._receiver_running:
            raise RuntimeError(parse_message(RECEIVER_OFF, OBJECTIVE="get"))
        
        response = []
        rid_founds = rids.copy()

        async def _getter():
            while True:
                emails = self._handler.emails

                for email in emails:
                    if not email.rid in rid_founds:

                        rid_founds.append(email.rid)

                        response.append(email)

                    if response:
                        return response

                await asyncio.sleep(WAIT_EMAIL_COOLDOWN)

        try:
            emails = await asyncio.wait_for(_getter(), timeout=timeout)
            return emails
        except asyncio.TimeoutError as tm_err:
            if raiser:
                raise tm_err
            

    def _get_handler(self, email_data: Email) -> EmailMessage:
        handler = EmailMessage()

        handler["From"] = email_data.sender 
        handler["To"] = email_data.destination
        handler["Subject"] = email_data.subject
        handler["Date"] = email_data.date
        handler.set_content(email_data.content)

        return handler
    

    def _add_attachments(self, handler: EmailMessage, **attachments):
        for att_name, path in attachments.items():
            if path:
                path = Path(path)
                mime_type, _ = mimetypes.guess_type(str(path))
                mime_type = mime_type or "application/octet-stream"
                main_type, sub_type = mime_type.split("/")
                
                if not path.exists():
                    raise PathNotFoundException(parse_message(PATH_NOT_FOUND, PATH=path, TYPE="attachment"))

                with path.file("rb") as file:        
                    content = file.read()

                    handler.add_attachment(
                        content,
                        maintype=main_type,
                        subtype=sub_type,
                        filename=att_name
                    )
            

    def send(self, email_data: Email|list[Email], timeout: Optional[float]=None) -> Report:
        """
        método responsável por enviar e-mails

        ### parâmetros:

            email_data (Email|list[Email]): instância da classe `Email`, que agrupa informações de um e-mail (tanto de enviados como de recebidos)
            timeout (Optional[float]): tempo máximo de espera até enviar um e-mail

        ### uso:

            email = Email(...)

            handler = EmailHandler(env_handler)
            handler.send(email)
        """
        
        def _send(email: Email):
            try:
                email.date = formatdate(localtime=True)
                email.gen_rid()
                handler = self._get_handler(email)

                if email.attachments:
                    self._add_attachments(handler, **email.attachments)

                with smtplib.SMTP("localhost", 1025) as smtp:
                    smtp.send_message(handler)

                return STATUS_250
            except ConnectionRefusedError:
                return STATUS_500

        if isinstance(email_data, list):
            report = Report(STATUS_250)
            for email in email_data:
                resp = _send(email)
                if resp != STATUS_250:
                    report.status = STATUS_200
                    report.error.append(email)
            
            if len(report) == len(email_data):
                report.status = STATUS_500

            return report
        resp = _send(email_data)
        return Report(
            status=resp,
            error=[email_data] if resp == STATUS_500 else []
        )
    

    @overload
    async def wait_emails(self, /, repeat: Optional[int]=None, timeout: Optional[float]=None, raiser: bool=True) -> AsyncGenerator[Email]: ...

    @overload
    async def wait_emails(self, address: str, repeat: Optional[int]=None, timeout: Optional[float]=None, raiser: bool=True) -> AsyncGenerator[Email]: ...

    async def wait_emails(self, address: Optional[str]=None, repeat: Optional[int]=None, timeout: Optional[float]=None, raiser: bool=True) -> AsyncGenerator[Email]:
        """
        aguarda e-mails e retorna-os, podendo filtrá-los baseado em um endereço de e-mail específico.

        ### parâmetros:
         
            address (str|None): endereço de e-mail que será usado como base para filtrar os e-mails recebidos (quando None retorna todos os e-mails obtidos)
            repeat: (int|None): quantidade de vezes que o receptor irá receber e-mails antes de parar (quando None não possui limites)
            timeout (float|None): tempo máximo de espera até receber um e-mail (quando None não possui tempo máximo)
            raiser (bool): se True levanta um erro - TimeoutError - quando timeout é excedido sem receber nenhum e-mail

        ### uso:

            handler = EmailHandler(env_handler)

            async def function_example():
                with handler:
                    emails = handler.wait_emails(...)

                    async for email in emails:
                        print(f"de: {email.sender} | para: {email.destination}") # de: sender@example.com | para: destination@example.com

            observação: caso você queira filtrar somente os e-mails enviados para um endereço de e-mail específico, adicione o parâmetro `address`:

                emails = handler.wait_emails(address="destination@example.com", ...)       
  
        """

        if not self._receiver_running:
            raise RuntimeError(parse_message(RECEIVER_OFF, OBJECTIVE="wait"))
        
        rid_founds = []

        while repeat is None or repeat > 0:
            emails = await self._get_emails(rid_founds, timeout, raiser)
            if emails is None:
                break
            
            for email in emails:
                rid_founds.append(email.rid)

                if address is not None and address not in email.destination:
                    continue

                if address:
                    email.destination = [address]

                yield email

                if repeat is not None:
                    if repeat > 0:
                        repeat -= 1
                    else:
                        break

            await asyncio.sleep(WAIT_EMAIL_COOLDOWN)


    def save_in(self, path: Path, extension: str=".txt"):
        """
        adiciona um caminho base onde os e-mails recebidos serão salvos

        ### parâmetros:

            paths (str|tuple[str]): sequência de caminhos que referenciam diretórios e subdiretórios
            extension (str): extensão do arquivo que armazenará o conteúdo do e-mail terá (padrão .txt)

        ### uso:

            handler = EmailHandler(env_handler)
            handler.save_in(".", "project_name", "emails", extension=".txt") # resultado: "./project_name/emails/

        todos os e-mails recebidos serão salvos a partir do caminho base, com diretórios (baseados no endereço de e-mail) e subdiretórios (baseados no assunto do e-mail) próprios:

            ./project_name/emails/
                address1_example.com/
                    subject_1/
                        content.txt - conteúdo do e-mail
                        metadata.json - metadados contendo informações sobre o e-mail
                        ... - possíveis anexos que foram enviados no e-mail
                    subject_2/
                        ...
                address2_example.com/
                    subject_1/
                        ...
                ...

            os pontos especias, como "@", "/", "-", etc, são convertidos em "_"
            
        """
        self.path = path
        self.path.mkdir(True)
        self.extension = str(extension).lower()

    
    def open(self):
        """
        abre o servidor, permitindo receber e-mails

        ### uso:

            handler = EmailHandler(env_handler)

            async def function_example():
                handler.open()

                emails = handler.wait_emails(...)

                async for email in emails:
                    ...

        ### sugestão:

            - para abrir e fechar o servidor SMTP e receber e-mails use o gerenciador de contexto with:

                async def function_example():
                    with handler:
                        emails = handler.wait_emails(...)

                        async for email in emails:
                            ...
        """
        if not self.receiver_running:
            self._controller.start()
            self._receiver_running = True


    def close(self) -> None:
        """
        fecha o servidor SMTP caso esteja aberto

        ### uso:

            handler = EmailHandler(env_handler)

            async def function_example():
                handler.open()

                emails = handler.wait_emails(...)

                async for email in emails:
                    ...

                handler.close()

         ### sugestão:

            - para abrir e fechar o servidor SMTP e receber e-mails use o gerenciador de contexto with:

                async def function_example():
                    with handler:
                        emails = handler.wait_emails(...)

                        async for email in emails:
                            ...
        """
        if self.receiver_running:
            self._controller.stop()
            self._receiver_running = False

    
    def __enter__(self) -> None:
        self.open()
    

    def __exit__(self, *args, **kwargs):
        self.close()
        return False
    
    
    def __repr__(self):
        receiver = "on" if self._receiver_running else "off"
        return f"<EmailHandler receiver={receiver} save={"off" if not self.path else str(self.path)} extension={self.extension} env={self._env}>"



__all__ = ["EmailHandler"]