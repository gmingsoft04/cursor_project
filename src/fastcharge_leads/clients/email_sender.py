"""SMTP email sending adapter."""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr


@dataclass(frozen=True, slots=True)
class SmtpConfig:
    host: str
    port: int
    username: str | None = None
    password: str | None = None
    from_email: str | None = None
    from_name: str | None = None
    use_tls: bool = True


class SmtpEmailSender:
    def __init__(self, config: SmtpConfig) -> None:
        self.config = config

    def send(self, *, to_email: str, subject: str, body: str) -> None:
        if not self.config.host:
            raise ValueError("SMTP_HOST is required to send approved outreach emails.")
        from_email = self.config.from_email or self.config.username
        if not from_email:
            raise ValueError("SMTP_FROM_EMAIL or SMTP_USERNAME is required to send emails.")

        message = EmailMessage()
        message["To"] = to_email
        message["From"] = formataddr((self.config.from_name or "", from_email))
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(self.config.host, self.config.port, timeout=30) as smtp:
            if self.config.use_tls:
                smtp.starttls()
            if self.config.username and self.config.password:
                smtp.login(self.config.username, self.config.password)
            smtp.send_message(message)
