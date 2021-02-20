from typing import Optional
import logging
from logging.config import dictConfig
import sys

from .config import get_logging_config, ConfigMode


def configure_logging(mode: Optional[ConfigMode] = None):
    logging_config = get_logging_config()

    if logging_config:
        if mode and mode.value in logging_config:
            dictConfig(logging_config[mode.value])
        else:
            dictConfig(logging_config)
    else:
        logger = logging.getLogger("rich_traceroute")
        logger.setLevel("INFO")
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s PID=%(process)d T=%(threadName)s %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logging.getLogger(
            "rich_traceroute.enrichers.async_channel"
        ).setLevel("INFO")
        logging.getLogger(
            "rich_traceroute.enrichers.async_connection"
        ).setLevel("INFO")
