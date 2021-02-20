import logging
import threading
import datetime

from ..config import TRACEROUTE_EXPIRY, IP_INFO_EXPIRY, HOUSEKEEPER_INTERVAL
from ..ip_info_db import IPInfo_Prefix
from ..traceroute import Traceroute


LOGGER = logging.getLogger(__name__)


def _setup_thread(interval: int):
    thread = threading.Timer(interval, _run_housekeeper)
    thread.name = "HouseKeeper"
    thread.start()


def _run_housekeeper():
    try:
        LOGGER.info("Running the housekeeper")

        Traceroute.delete().where(
            Traceroute.created < datetime.datetime.utcnow() - TRACEROUTE_EXPIRY
        ).execute()

        IPInfo_Prefix.delete().where(
            IPInfo_Prefix.last_updated < datetime.datetime.utcnow() - IP_INFO_EXPIRY
        ).execute()

        LOGGER.info("Housekeeper completed")
    except:  # noqa: E722
        LOGGER.exception(
            "Unhandled exception while running the housekeeper"
        )

    _setup_thread(HOUSEKEEPER_INTERVAL)


def setup_housekeeper():

    # At app setup time, run the housekeeper immediately; once
    # the app is running, it will be executed on the basis of
    # the regular  interval.
    _setup_thread(1)
