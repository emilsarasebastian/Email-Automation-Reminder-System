"""
email_builder.py - Turn plain text into a proper email message object.
"""

from email.message import EmailMessage
from email.utils import formataddr


def build_email(
    sender_name: str,
    sender_email: str,
    to_name: str,
    to_email: str,
    subject: str,
    body: str,
) -> EmailMessage:
    """Create an EmailMessage ready to be sent by smtplib."""
    msg = EmailMessage()
    msg["From"] = formataddr((sender_name, sender_email or "noreply@example.com"))
    msg["To"] = formataddr((to_name, to_email))
    msg["Subject"] = subject
    msg.set_content(body)
    return msg
