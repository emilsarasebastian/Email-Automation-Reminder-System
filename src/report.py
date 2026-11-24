"""
report.py - Save results to a CSV report and print a summary.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

REPORT_COLUMNS = [
    "timestamp", "reminder_id", "contact_id", "name", "email",
    "subject", "mode", "status", "error",
]


def write_report(results: List[dict], outputs_dir: Path) -> Optional[Path]:
    """Write outputs/email_report_<timestamp>.csv and return its path."""
    if not results:
        return None
    outputs_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(results, columns=REPORT_COLUMNS)
    path = outputs_dir / f"email_report_{datetime.now():%Y%m%d_%H%M%S}.csv"
    df.to_csv(path, index=False)
    return path


def summarize(results: List[dict]) -> str:
    """Return a short text summary (counts per status and per reminder)."""
    if not results:
        return "No reminders were due. Nothing to do."
    df = pd.DataFrame(results, columns=REPORT_COLUMNS)
    lines = ["", "=" * 50, "RUN SUMMARY", "=" * 50, f"Total attempts : {len(df)}"]
    for status, count in df["status"].value_counts().items():
        lines.append(f"{status:<15}: {count}")
    lines.append("-" * 50)
    for rid, group in df.groupby("reminder_id"):
        counts = ", ".join(f"{s}={n}" for s, n in group["status"].value_counts().items())
        lines.append(f"Reminder {rid:<6}: {counts}")
    lines.append("=" * 50)
    return "\n".join(lines)
