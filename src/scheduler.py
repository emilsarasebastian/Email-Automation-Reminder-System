"""
scheduler.py - Run a job again and again on a timer.

Uses the popular `schedule` library when installed. If it is missing,
a tiny built-in loop does the same job, so the project never breaks.
"""

import logging
import time
from typing import Callable

logger = logging.getLogger("email_automation")


def run_forever(job: Callable[[], None], interval_minutes: float) -> None:
    """Call `job()` immediately, then every `interval_minutes` until Ctrl+C."""
    logger.info("Scheduler started: checking every %s minute(s). Press Ctrl+C to stop.", interval_minutes)
    try:
        try:
            import schedule

            schedule.every(interval_minutes).minutes.do(job)
            job()
            while True:
                schedule.run_pending()
                time.sleep(1)
        except ImportError:
            logger.info("'schedule' package not installed - using built-in timer loop")
            while True:
                job()
                time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")
