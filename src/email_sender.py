"""
email_sender.py - Send emails through SMTP (or pretend to, in dry-run mode).

Dry-run mode never opens a network connection. It is the default so a
student can never email real people by accident.
"""

import logging
import smtplib
import time
from email.message import EmailMessage
from typing import Optional, Tuple

from src.config import SMTPSettings

logger = logging.getLogger("email_automation")

STATUS_SENT = "SENT"
STATUS_FAILED = "FAILED"
STATUS_DRY_RUN = "DRY_RUN"


class EmailSender:
    def __init__(self, settings: SMTPSettings, dry_run: bool = True, max_retries: int = 2):
        self.settings = settings
        self.dry_run = dry_run
        self.max_retries = max_retries
        self._server: Optional[smtplib.SMTP] = None

    # ---- connection handling -------------------------------------------------
    def connect(self) -> None:
        """Open one SMTP connection that is reused for all emails."""
        if self.dry_run:
            return
        s = self.settings
        if s.port == 465:  # implicit SSL
            server = smtplib.SMTP_SSL(s.host, s.port, timeout=30)
        else:  # 587: start plain, then upgrade with STARTTLS
            server = smtplib.SMTP(s.host, s.port, timeout=30)
            server.starttls()
        server.login(s.sender_email, s.sender_password)
        self._server = server
        logger.info("Connected to SMTP server %s:%s", s.host, s.port)

    def close(self) -> None:
        if self._server is not None:
            try:
                self._server.quit()
            except smtplib.SMTPException:
                pass
            self._server = None

    # ---- sending -------------------------------------------------------------
    def send(self, msg: EmailMessage) -> Tuple[str, str]:
        """Send one email. Returns (status, error_message)."""
        if self.dry_run:
            return STATUS_DRY_RUN, ""

        last_error = ""
        for attempt in range(1, self.max_retries + 2):
            try:
                if self._server is None:
                    self.connect()
                self._server.send_message(msg)
                time.sleep(self.settings.delay_seconds)
                return STATUS_SENT, ""
            except smtplib.SMTPAuthenticationError as exc:
                # Wrong password: retrying will not help.
                return STATUS_FAILED, f"Authentication failed: {exc.smtp_code}"
            except (smtplib.SMTPException, OSError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                logger.warning("Attempt %d failed: %s", attempt, last_error)
                self.close()  # force a fresh connection on the next attempt
                time.sleep(self.settings.delay_seconds)
        return STATUS_FAILED, last_error
