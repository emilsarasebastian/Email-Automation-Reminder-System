"""
engine.py - The core workflow:

    contacts + reminders -> pick due reminders -> personalize -> send -> track -> report
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

import pandas as pd

from src import config
from src.data_loader import load_contacts, load_reminders
from src.email_builder import build_email
from src.email_sender import STATUS_DRY_RUN, STATUS_FAILED, EmailSender
from src.template_engine import load_template, render

logger = logging.getLogger("email_automation")

STATUS_SKIPPED = "SKIPPED"
HISTORY_FILE = "send_history.csv"


# ---- send history (prevents emailing the same person twice) -----------------
def _load_history(outputs_dir: Path) -> Set[str]:
    path = outputs_dir / HISTORY_FILE
    if not path.exists():
        return set()
    return set(pd.read_csv(path, dtype=str)["key"])


def _append_history(outputs_dir: Path, key: str) -> None:
    outputs_dir.mkdir(parents=True, exist_ok=True)
    path = outputs_dir / HISTORY_FILE
    new_file = not path.exists()
    with open(path, "a", encoding="utf-8") as f:
        if new_file:
            f.write("key\n")
        f.write(f"{key}\n")


def _result(reminder_id, contact, subject, mode, status, error="") -> dict:
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reminder_id": reminder_id,
        "contact_id": contact.get("contact_id", ""),
        "name": contact.get("name", ""),
        "email": contact.get("email", ""),
        "subject": subject,
        "mode": mode,
        "status": status,
        "error": error,
    }


def select_due(reminders: pd.DataFrame, now: datetime, process_all: bool) -> List[dict]:
    """Return reminder rows whose scheduled time has arrived (or all, if asked)."""
    due = []
    for row in reminders.to_dict("records"):
        when = row["scheduled_at"]
        if when is None or pd.isna(when):
            logger.error("Reminder %s has an invalid date/time - skipped", row["reminder_id"])
            continue
        if process_all or when <= now:
            due.append(row)
    return due


def run_batch(
    now: Optional[datetime] = None,
    dry_run: bool = True,
    process_all: bool = False,
    settings: Optional[config.SMTPSettings] = None,
    contacts_path: Path = config.CONTACTS_FILE,
    reminders_path: Path = config.REMINDERS_FILE,
    templates_dir: Path = config.TEMPLATES_DIR,
    outputs_dir: Path = config.OUTPUTS_DIR,
) -> List[dict]:
    """Process every due reminder once and return a list of result records."""
    now = now or datetime.now()
    settings = settings or config.get_smtp_settings()
    mode = "dry-run" if dry_run else "live"

    contacts = load_contacts(contacts_path)
    reminders = load_reminders(reminders_path)
    due = select_due(reminders, now, process_all)
    logger.info("[%s] %d reminder(s) due as of %s", mode, len(due), now.strftime("%Y-%m-%d %H:%M"))

    history = set() if dry_run else _load_history(outputs_dir)
    sender = EmailSender(settings, dry_run=dry_run)
    results: List[dict] = []
    previews: List[str] = []  # full text of each email (dry-run only)

    try:
        sender.connect()
        for rem in due:
            rid = rem["reminder_id"]
            try:
                template_text = load_template(templates_dir, rem["template"])
            except FileNotFoundError as exc:
                logger.error("Reminder %s: %s", rid, exc)
                results.append(_result(rid, {}, rem["subject"], mode, STATUS_FAILED, str(exc)))
                continue

            group = rem["group"]
            recipients = contacts if group.lower() == "all" else contacts[contacts["group"] == group]
            if recipients.empty:
                logger.warning("Reminder %s: no contacts in group '%s'", rid, group)

            for contact in recipients.to_dict("records"):
                # Context = every reminder column + contact details + sender name
                context = {**rem, **contact, "sender_name": settings.sender_name}
                subject = render(rem["subject"], context)
                key = f"{rid}|{contact['email']}"

                if key in history:
                    results.append(_result(rid, contact, subject, mode, STATUS_SKIPPED, "Already sent"))
                    logger.info("SKIPPED %s (already sent) -> %s", rid, contact["email"])
                    continue
                if not contact["email_valid"]:
                    results.append(_result(rid, contact, subject, mode, STATUS_FAILED, "Invalid email address"))
                    logger.error("FAILED  %s -> %s (invalid email address)", rid, contact["email"])
                    continue

                body = render(template_text, context)
                msg = build_email(
                    settings.sender_name, settings.sender_email,
                    contact["name"], contact["email"], subject, body,
                )
                status, error = sender.send(msg)
                results.append(_result(rid, contact, subject, mode, status, error))
                if dry_run:
                    previews.append(msg.as_string())

                if status == STATUS_FAILED:
                    logger.error("FAILED  %s -> %s (%s)", rid, contact["email"], error)
                else:
                    logger.info("%-7s %s -> %s | %s", status, rid, contact["email"], subject)
                    if not dry_run:
                        _append_history(outputs_dir, key)
    finally:
        sender.close()

    if previews:
        outputs_dir.mkdir(parents=True, exist_ok=True)
        divider = "\n" + "=" * 60 + "\n"
        (outputs_dir / "dry_run_preview.txt").write_text(divider.join(previews), encoding="utf-8")
        logger.info("Rendered email preview saved: outputs/dry_run_preview.txt")

    return results
