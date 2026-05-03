import logging
import os
from logging.handlers import TimedRotatingFileHandler


_LOG_DIR = ".codeprism/logs"
_LOG_FILE = os.path.join(_LOG_DIR, "codeprism.log")


def setup_logger(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger()

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    os.makedirs(_LOG_DIR, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        _LOG_FILE, when="midnight", backupCount=7, encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
