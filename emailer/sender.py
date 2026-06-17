from __future__ import annotations

import mimetypes
import smtplib
from email.message import EmailMessage
from pathlib import Path

from config.settings import SMTPSettings


class EmailSender:
    def __init__(self, settings: SMTPSettings):
        self.settings = settings

    def send(self, to_email: str, subject: str, body: str, attachments: list[Path]) -> None:
        if not self.settings.is_complete:
            raise ValueError("SMTP settings are incomplete.")

        message = EmailMessage()
        message["From"] = self.settings.username
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        for attachment in attachments:
            self._attach_file(message, attachment)

        with smtplib.SMTP(self.settings.host, self.settings.port, timeout=30) as server:
            server.starttls()
            server.login(self.settings.username, self.settings.password)
            server.send_message(message)

    @staticmethod
    def _attach_file(message: EmailMessage, path: Path) -> None:
        if not path.exists() or path.suffix.lower() != ".pdf":
            raise ValueError(f"Invalid PDF attachment: {path.name}")

        content_type, _ = mimetypes.guess_type(path)
        maintype, subtype = (content_type or "application/pdf").split("/", 1)
        message.add_attachment(
            path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=path.name,
        )
