"""
config.py - Central place for paths and settings.

Secrets (email, password) are NEVER written in code. They are read from
environment variables, usually loaded from a local `.env` file that is
listed in .gitignore and therefore never uploaded to GitHub.
"""

import os
from dataclasses import dataclass
from pathlib import Path

# Project root = the folder that contains main.py
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUTS_DIR = BASE_DIR / "outputs"
LOGS_DIR = BASE_DIR / "logs"

CONTACTS_FILE = DATA_DIR / "contacts.csv"
REMINDERS_FILE = DATA_DIR / "reminders.csv"


def load_env() -> None:
    """Load variables from .env into os.environ.

    Uses python-dotenv when installed; otherwise falls back to a tiny
    parser so the project still works with zero extra packages.
    """
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path)
    except ImportError:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass
class SMTPSettings:
    """Everything needed to talk to an SMTP server."""

    host: str
    port: int
    sender_email: str
    sender_password: str
    sender_name: str
    delay_seconds: float  # pause between emails (be polite to the server)

    def has_credentials(self) -> bool:
        return bool(self.sender_email and self.sender_password)


def get_smtp_settings() -> SMTPSettings:
    """Read SMTP settings from environment variables."""
    load_env()
    return SMTPSettings(
        host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        port=int(os.getenv("SMTP_PORT", "587")),
        sender_email=os.getenv("SENDER_EMAIL", ""),
        sender_password=os.getenv("SENDER_PASSWORD", ""),
        sender_name=os.getenv("SENDER_NAME", "Automation Team"),
        delay_seconds=float(os.getenv("SEND_DELAY_SECONDS", "1")),
    )
