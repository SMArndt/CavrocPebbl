# src/logging_config.py

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_LEVEL = LOG_LEVEL = "DEBUG"  # os.getenv("LOG_LEVEL", "INFO").upper()

os.makedirs(LOG_DIR, exist_ok=True)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

max_bytes = int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024))  # default 10MB
backup_count = int(os.getenv("LOG_BACKUP_COUNT", 5))  # default keep 5 backups
file_handler = RotatingFileHandler(
    f"{LOG_DIR}/app.log", maxBytes=max_bytes, backupCount=backup_count
)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger = logging.getLogger("rocbox")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False


def get_logger(name: str = "rocbox") -> logging.Logger:
    return logging.getLogger(name)


def log_request(message: str, label: str = "ℹ️ Request") -> None:
    logger.info(f"{label} | {message}")


def log_error(message: str, label: str = "❌ Error") -> None:
    logger.error(f"{label} | {message}")
