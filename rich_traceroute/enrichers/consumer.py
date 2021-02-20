from __future__ import annotations
from typing import List
import json
import threading
import queue
import logging
import functools


from .enricher import Enricher
from .async_connection import AsyncConnection, Reconnector
from .async_channel import EnrichmentJobsChannel, IPDBInfoChannel
from ..structures import IPDBInfo, EnricherJob

LOGGER = logging.getLogger(__name__)


def log_exception(function):

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except:  # noqa: E722
            LOGGER.exception(f"Unhandled exception in {function.__name__}")
            raise

    return wrapper


class ConsumerAsyncConnection(AsyncConnection):

    def __init__(self, consumer: ConsumerThread):
        super().__init__()

        self.consumer: ConsumerThread = consumer

    def _setup_channels(self):

        enrichment_jobs_channel = EnrichmentJobsChannel(
            name="enrichment_jobs_channel",
            connection=self.connection,
            close_connection=self.close_connection,
            on_message=self.consumer.receive_traceroute_enrichment_job
        )
        self._channels.append(enrichment_jobs_channel)

        ip_db_info_channel = IPDBInfoChannel(
            name="ip_db_info_channel",
            connection=self.connection,
            close_connection=self.close_connection,
            on_message=self.consumer.receive_ip_info_data
        )
        self._channels.append(ip_db_info_channel)


class ConsumerThread(threading.Thread):

    def __init__(self, consumer_thread_name: str, enrichers_per_consumer: int):
        super().__init__(name=consumer_thread_name)

        self.daemon = True

        self.enrichment_jobs_queue: queue.Queue = queue.Queue()

        self.enrichers: List[Enricher] = []

        for n in range(enrichers_per_consumer):
            enricher_thread = Enricher(
                f"{consumer_thread_name}-enricher-{n}",
                self.enrichment_jobs_queue
            )

            self.enrichers.append(enricher_thread)
            enricher_thread.start()

        self.connection = Reconnector(
            ConsumerAsyncConnection,
            self
        )

    def run(self):
        LOGGER.debug("Starting ConsumerThread")
        self.connection.run()
        LOGGER.debug("ConsumerThread completed")

    def stop(self):
        LOGGER.debug("Stopping enrichers...")
        for enricher in self.enrichers:
            enricher.stop()

        LOGGER.debug("Stopping the connection...")
        self.connection.stop()

    @log_exception
    def receive_ip_info_data(self, ch, method, properties, body):
        LOGGER.debug(f"Got IP DB info data: {body.decode()}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

        data = json.loads(body)

        ip_info = IPDBInfo.from_dict(data)

        for enricher in self.enrichers:
            enricher.add_ip_info_to_local_cache(ip_info, False)

    @log_exception
    def receive_traceroute_enrichment_job(self, ch, method, properties, body):
        if self.enrichment_jobs_queue.qsize() == 0:
            LOGGER.debug(f"Got a job: {body.decode()}")

            ch.basic_ack(delivery_tag=method.delivery_tag)

            data = json.loads(body)

            job = EnricherJob.from_dict(data)

            self.enrichment_jobs_queue.put(job)

            return

        LOGGER.debug(f"Job rejected: {body.decode()}")

        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def setup_consumers(consumers: int = 1, enrichers_per_consumer: int = 3) -> List[ConsumerThread]:
    threads = []
    for n in range(consumers):
        thread = ConsumerThread(f"consumer-{n}", enrichers_per_consumer)
        threads.append(thread)
        thread.start()

    return threads
