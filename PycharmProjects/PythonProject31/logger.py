import logging
import sys
from logging.handlers import RotatingFileHandler

import config


def setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
    if root.handlers:
        return

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if not config.IS_SERVERLESS:
        try:
            config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

            main_handler = RotatingFileHandler(
                config.BOT_LOG_FILE,
                maxBytes=5 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            main_handler.setLevel(logging.INFO)
            main_handler.setFormatter(fmt)
            root.addHandler(main_handler)

            err_handler = RotatingFileHandler(
                config.ERROR_LOG_FILE,
                maxBytes=5 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            err_handler.setLevel(logging.ERROR)
            err_handler.setFormatter(fmt)
            root.addHandler(err_handler)
        except OSError:
            pass  # read-only FS (serverless) — faqat stdout

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    root.addHandler(console)

    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
