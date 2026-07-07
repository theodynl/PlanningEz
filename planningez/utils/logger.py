"""Logging configuration for PlanningEz."""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for PlanningEz.

    Args:
        level: Logging level (default: INFO)
    """
    # Create logs directory
    log_dir = Path.home() / ".planningez" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("planningez")
    logger.setLevel(level)

    # Create formatters
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    log_file = log_dir / f"planningez_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("Logging initialized")
