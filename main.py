"""
main.py - Command-line entry point for the Email Automation & Reminder System.

Examples
--------
python main.py --generate-sample     # create fresh dummy data (dates = today)
python main.py                       # DRY-RUN: due reminders only (safe default)
python main.py --all                 # DRY-RUN: every reminder, ignoring dates
python main.py --as-of "2026-11-25 10:30"   # pretend it is this date/time
python main.py --send                # LIVE: really sends via SMTP
python main.py --schedule --interval 5      # keep running, check every 5 minutes
"""

import argparse
import sys
from datetime import datetime

from src import config
from src.engine import run_batch
from src.logger_setup import setup_logging
from src.report import summarize, write_report
from src.sample_data import generate
from src.scheduler import run_forever


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Email Automation & Reminder System")
    p.add_argument("--send", action="store_true",
                   help="LIVE mode: really send emails (default is dry-run)")
    p.add_argument("--all", action="store_true",
                   help="process every reminder, ignoring send date/time")
    p.add_argument("--as-of", metavar="'YYYY-MM-DD HH:MM'",
                   help="simulate a different current date/time")
    p.add_argument("--schedule", action="store_true",
                   help="keep running and re-check on a timer")
    p.add_argument("--interval", type=float, default=1.0,
                   help="minutes between checks in --schedule mode (default 1)")
    p.add_argument("--generate-sample", action="store_true",
                   help="write fresh dummy contacts.csv and reminders.csv, then exit")
    p.add_argument("--yes", action="store_true",
                   help="skip the confirmation prompt in --send mode")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logger = setup_logging()

    if args.generate_sample:
        generate(config.DATA_DIR)
        logger.info("Sample data written to %s", config.DATA_DIR)
        return 0

    dry_run = not args.send
    now_override = None
    if args.as_of:
        try:
            now_override = datetime.strptime(args.as_of, "%Y-%m-%d %H:%M")
        except ValueError:
            logger.error("--as-of must look like '2026-11-25 10:30'")
            return 1

    settings = config.get_smtp_settings()
    if not dry_run:
        if not settings.has_credentials():
            logger.error("LIVE mode needs SENDER_EMAIL and SENDER_PASSWORD in your .env file.")
            return 1
        if not args.yes and input("LIVE mode will send REAL emails. Type 'yes' to continue: ").strip().lower() != "yes":
            logger.info("Cancelled.")
            return 0

    def job() -> None:
        try:
            results = run_batch(now=now_override, dry_run=dry_run,
                                process_all=args.all, settings=settings)
        except (FileNotFoundError, ValueError) as exc:
            logger.error("Setup problem: %s", exc)
            return
        report = write_report(results, config.OUTPUTS_DIR)
        print(summarize(results))
        if report:
            logger.info("Report saved: %s", report.relative_to(config.BASE_DIR))

    if args.schedule:
        run_forever(job, args.interval)
    else:
        job()
    return 0


if __name__ == "__main__":
    sys.exit(main())
