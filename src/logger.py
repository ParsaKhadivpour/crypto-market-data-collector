import logging
import sys
from logging.handlers import RotatingFileHandler
from src import config

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging()->None:
    """Configure logging once for the whole application"""
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    level = getattr(logging,config.LOG_LEVEL.upper(),logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT,DATE_FORMAT)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        config.LOG_DIR / "collector.log",
        maxBytes=1000000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root =  logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(console_handler)
    root.addHandler(file_handler)
    logging.getLogger("urllib3").setLevel(logging.WARNING)