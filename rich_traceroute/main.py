from typing import List
from threading import Thread
import logging
import os

from rich_traceroute.db import connect_to_the_db
from rich_traceroute.enrichers.consumer import setup_consumers
from rich_traceroute.enrichers.dispatcher import (
    setup_enrichment_jobs_dispatcher,
    setup_ipinfo_dispatcher
)
from rich_traceroute.enrichers.ixp_networks import setup_ixp_networks_updater
from rich_traceroute.housekeeping import setup_housekeeper
from rich_traceroute.config import load_config, ConfigMode
from rich_traceroute.logging_config import configure_logging
from rich_traceroute.metrics import configure_metrics


LOGGER = logging.getLogger(__name__)


def setup_environment(mode: ConfigMode) -> List[Thread]:

    res: List[Thread] = []

    cfg = load_config()

    configure_logging(mode)
    configure_metrics()

    LOGGER.info("Setting up the environment...")

    connect_to_the_db()

    LOGGER.info("Spinning up the workers [job dispatcher]...")
    res.append(setup_enrichment_jobs_dispatcher())

    if mode == ConfigMode.WORKER or os.environ.get("FLASK_DEBUG", 0) == "1":
        LOGGER.info("Spinning up the workers [consumers]...")
        consumers = setup_consumers(
            cfg["workers"]["consumers"],
            cfg["workers"]["enrichers"]
        )
        res.extend(consumers)

        LOGGER.info("Spinning up the workers [IP info dispatcher]...")
        res.append(setup_ipinfo_dispatcher())

        if os.environ.get("FLASK_DEBUG", 0) != "1":
            LOGGER.info("Spinning up the IXP Networks updater...")
            res.append(setup_ixp_networks_updater(consumers))

        LOGGER.info("Spinning up the house keeper...")
        res.append(setup_housekeeper())

    LOGGER.info("Environment setup completed")

    return res


def main():
    threads = setup_environment(ConfigMode.WORKER)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
