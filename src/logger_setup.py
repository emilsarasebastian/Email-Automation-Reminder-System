"""
logger_setup.py - Configure logging to both the terminal and a log file.

Every send attempt (success or failure) ends up in logs/email_automation.log,
which is useful proof-of-work and for debugging.
"""

import logging
from pathlib import Path

from src.config import LOGS_DIR

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"


def setup_logging(log_dir: Path = LOGS_DIR) -> logging.Logger:
    """Create (or reuse) the project logger."""
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("email_automation")
    if logger.handlers:  # already configured, avoid duplicate lines
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler(log_dir / "email_automation.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    return logger
