"""
sample_data.py - Generate dummy contacts and reminders for safe testing.

All addresses use the reserved domain example.com, which can never belong
to a real person. Reminder dates are created relative to *today* so the
demo always has some reminders that are due and some still in the future.
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path

CONTACTS = [
    ("C001", "Asha Verma", "asha.verma@example.com", "Students", "Python Batch 12"),
    ("C002", "Rohan Mehta", "rohan.mehta@example.com", "Students", "Python Batch 12"),
    ("C003", "Priya Nair", "priya.nair@example.com", "Students", "Python Batch 12"),
    ("C004", "Vikram Singh", "vikram.singh@example.com", "Sales", "Acme Traders"),
    ("C005", "Neha Kapoor", "neha.kapoor@example.com", "Sales", "Bright Solutions"),
    ("C006", "Imran Khan", "imran.khan@example.com", "Sales", "Orbit Retail"),
    ("C007", "Sara Thomas", "sara.thomas@example.com", "HR", "Internal"),
    ("C008", "Karan Joshi", "karan.joshi@example.com", "HR", "Internal"),
    ("C009", "Meera Iyer", "meera.iyer@example.com", "Operations", "Internal"),
    ("C010", "Arjun Reddy", "arjun.reddy@example.com", "Operations", "Internal"),
    # Deliberately broken address -> demonstrates failure logging
    ("C011", "Test Invalid", "invalid-email.example.com", "Operations", "Internal"),
]

REMINDER_HEADER = [
    "reminder_id", "group", "template", "subject", "send_date", "send_time",
    "event_name", "event_date", "event_time", "link",
    "invoice_no", "amount", "due_date", "task_name", "task_deadline",
]


def generate(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now()
    d = lambda days: (today + timedelta(days=days)).strftime("%Y-%m-%d")

    with open(data_dir / "contacts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["contact_id", "name", "email", "group", "company"])
        w.writerows(CONTACTS)

    blank = lambda **kw: [kw.get(c, "") for c in REMINDER_HEADER]
    rows = [
        blank(reminder_id="R001", group="Students", template="webinar_reminder",
              subject="Reminder: {event_name} starts soon", send_date=d(0), send_time="00:01",
              event_name="Python Automation Webinar", event_date=d(1), event_time="11:00 AM IST",
              link="https://example.com/webinar"),
        blank(reminder_id="R002", group="Sales", template="payment_reminder",
              subject="Payment reminder: Invoice {invoice_no}", send_date=d(0), send_time="00:02",
              invoice_no="INV-2026-014", amount="INR 12,500", due_date=d(3)),
        blank(reminder_id="R003", group="Operations", template="meeting_alert",
              subject="Meeting alert: {event_name}", send_date=d(0), send_time="00:03",
              event_name="Weekly Ops Review", event_date=d(1), event_time="10:00 AM IST",
              link="https://example.com/ops-meet"),
        blank(reminder_id="R004", group="HR", template="task_notification",
              subject="Task assigned: {task_name}", send_date=d(1), send_time="09:30",
              task_name="Update onboarding checklist", task_deadline=d(4)),
        blank(reminder_id="R005", group="Students", template="webinar_reminder",
              subject="Starting in 1 hour: {event_name}", send_date=d(1), send_time="10:00",
              event_name="Python Automation Webinar", event_date=d(1), event_time="11:00 AM IST",
              link="https://example.com/webinar"),
    ]
    with open(data_dir / "reminders.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(REMINDER_HEADER)
        w.writerows(rows)
