"""
data_loader.py - Read and validate the contact and reminder CSV files.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

CONTACT_COLUMNS = {"contact_id", "name", "email", "group"}
REMINDER_COLUMNS = {"reminder_id", "group", "template", "subject", "send_date", "send_time"}

# A simple email check. Good enough to catch typos like "john.gmail.com".
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match((email or "").strip()))


def _read_csv(path: Path, required: set) -> pd.DataFrame:
    """Read a CSV as text, strip whitespace, and check required columns exist."""
    if not Path(path).exists():
        raise FileNotFoundError(f"File not found: {path}")
    df = pd.read_csv(path, dtype=str).fillna("")
    df.columns = [c.strip() for c in df.columns]
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{Path(path).name} is missing columns: {sorted(missing)}")
    return df.apply(lambda col: col.str.strip())


def load_contacts(path: Path) -> pd.DataFrame:
    """Load contacts. Adds a boolean column `email_valid`."""
    df = _read_csv(path, CONTACT_COLUMNS)
    df["email_valid"] = df["email"].apply(is_valid_email)
    return df


def parse_schedule(send_date: str, send_time: str) -> Optional[datetime]:
    """Combine 'YYYY-MM-DD' and 'HH:MM' into a datetime. Returns None if invalid."""
    try:
        return datetime.strptime(f"{send_date} {send_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def load_reminders(path: Path) -> pd.DataFrame:
    """Load reminders. Adds a `scheduled_at` column (datetime or None)."""
    df = _read_csv(path, REMINDER_COLUMNS)
    df["scheduled_at"] = [
        parse_schedule(d, t) for d, t in zip(df["send_date"], df["send_time"])
    ]
    return df
