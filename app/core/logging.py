import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure application-wide logging.

    Third-party libraries are kept at WARNING to reduce noise. Never log
    secrets (bot tokens, encryption keys) anywhere in the codebase.
    """
    root = logging.getLogger()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.handlers.clear()
    root.addHandler(handler)

    for noisy_logger in ("aiogram.event", "aiogram.dispatcher", "sqlalchemy.engine"):
        logging.getLogger(noisy_logger).setLevel("WARNING")
