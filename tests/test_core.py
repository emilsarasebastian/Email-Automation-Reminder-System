"""
Basic tests. Run from the project root with:   python -m unittest discover -s tests -v
No real emails are sent: SMTP is replaced with a mock.
"""

import smtplib
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import SMTPSettings
from src.data_loader import is_valid_email
from src.email_builder import build_email
from src.email_sender import EmailSender
from src.engine import run_batch
from src.sample_data import generate
from src.template_engine import render

SETTINGS = SMTPSettings("localhost", 587, "me@example.com", "pw", "Tester", 0)
ROOT = Path(__file__).resolve().parent.parent


class TemplateTests(unittest.TestCase):
    def test_render_fills_placeholders(self):
        self.assertEqual(render("Hi {name}", {"name": "Asha"}), "Hi Asha")

    def test_render_keeps_unknown_placeholder(self):
        self.assertEqual(render("Link: {link}", {}), "Link: {link}")


class ValidationTests(unittest.TestCase):
    def test_valid_and_invalid_emails(self):
        self.assertTrue(is_valid_email("a.b@example.com"))
        self.assertFalse(is_valid_email("a.b.example.com"))
        self.assertFalse(is_valid_email(""))


class SenderTests(unittest.TestCase):
    def _msg(self):
        return build_email("Me", "me@example.com", "You", "you@example.com", "Hi", "Body")

    def test_dry_run_makes_no_connection(self):
        with patch("smtplib.SMTP") as smtp:
            status, _ = EmailSender(SETTINGS, dry_run=True).send(self._msg())
        self.assertEqual(status, "DRY_RUN")
        smtp.assert_not_called()

    def test_live_send_success(self):
        with patch("smtplib.SMTP") as smtp:
            status, err = EmailSender(SETTINGS, dry_run=False).send(self._msg())
        self.assertEqual((status, err), ("SENT", ""))
        smtp.return_value.send_message.assert_called_once()

    def test_live_send_failure_is_reported(self):
        server = MagicMock()
        server.send_message.side_effect = smtplib.SMTPRecipientsRefused({})
        with patch("smtplib.SMTP", return_value=server):
            status, err = EmailSender(SETTINGS, dry_run=False, max_retries=1).send(self._msg())
        self.assertEqual(status, "FAILED")
        self.assertIn("SMTPRecipientsRefused", err)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        generate(self.tmp)
        self.kwargs = dict(
            settings=SETTINGS,
            contacts_path=self.tmp / "contacts.csv",
            reminders_path=self.tmp / "reminders.csv",
            templates_dir=ROOT / "templates",
            outputs_dir=self.tmp / "out",
        )

    def test_dry_run_all_covers_every_contact_once(self):
        results = run_batch(dry_run=True, process_all=True, **self.kwargs)
        statuses = {r["status"] for r in results}
        self.assertEqual(statuses, {"DRY_RUN", "FAILED"})  # invalid email fails
        failed = [r for r in results if r["status"] == "FAILED"]
        # Only contact C011 (Operations) has a bad address, and only R003 targets Operations
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["email"], "invalid-email.example.com")

    def test_future_reminders_not_due(self):
        results = run_batch(now=datetime(2000, 1, 1), dry_run=True, **self.kwargs)
        self.assertEqual(results, [])

    def test_live_mode_skips_already_sent(self):
        with patch("smtplib.SMTP"):
            first = run_batch(dry_run=False, process_all=True, **self.kwargs)
            second = run_batch(dry_run=False, process_all=True, **self.kwargs)
        self.assertIn("SENT", {r["status"] for r in first})
        self.assertNotIn("SENT", {r["status"] for r in second})
        self.assertIn("SKIPPED", {r["status"] for r in second})


if __name__ == "__main__":
    unittest.main()
