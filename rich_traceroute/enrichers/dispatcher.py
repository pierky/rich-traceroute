from __future__ import annotations
from typing import Optional, Type
import json
import threading
import logging
import queue

from .async_connection import AsyncConnection, Reconnector
from .async_channel import AsyncChannel, TracerouteDispatcherChannel, IPDBInfoChannel
from ..structures import EnricherJob, IPDBInfo


LOGGER = logging.getLogger(__name__)


enrichment_jobs_dispatcher: EnrichmentJobsDispatcher
ipinfo_dispatcher: IPInfoDispatcher


class DispatcherAsyncConnection(AsyncConnection):

    def __init__(self, channel_class: AsyncChannel, channel_name: str, queue: queue.Queue):
        super().__init__()

        self.channel_class = channel_class
        self.channel_name = channel_name
        self.queue = queue

        self.channel: AsyncChannel

    def _setup_channels(self):
        self.channel = self.channel_class(
            name=self.channel_name,
            connection=self.connection,
            close_connection=self.close_connection,
            get_message_to_publish=self.get_message_to_publish
        )
        self._channels.append(self.channel)

    def get_message_to_publish(self) -> Optional[str]:
        try:
            job = self.queue.get(block=False)
        except queue.Empty:
            return None

        return json.dumps(job.to_json_dict())


class DispatcherThread(threading.Thread):

    CHANNEL_CLASS: Type[AsyncChannel]
    CHANNEL_NAME: str

    def __init__(self):
        super().__init__(name="dispatcher")

        self.daemon = True

        self.queue = queue.Queue()

        self.reconnector = Reconnector(
            DispatcherAsyncConnection,
            self.CHANNEL_CLASS, self.CHANNEL_NAME, self.queue
        )

    def run(self):
        LOGGER.debug("Starting DispatcherThread")
        self.reconnector.run()
        LOGGER.debug("DispatcherThread completed")

    def stop_dispatcher(self):
        self.reconnector.stop()


class EnrichmentJobsDispatcher(DispatcherThread):

    CHANNEL_CLASS = TracerouteDispatcherChannel
    CHANNEL_NAME = "traceroute_dispatcher"


class IPInfoDispatcher(DispatcherThread):

    CHANNEL_CLASS = IPDBInfoChannel
    CHANNEL_NAME = "ipinfo_dispatcher"


def setup_enrichment_jobs_dispatcher() -> EnrichmentJobsDispatcher:
    global enrichment_jobs_dispatcher

    enrichment_jobs_dispatcher = EnrichmentJobsDispatcher()
    enrichment_jobs_dispatcher.start()

    return enrichment_jobs_dispatcher


def setup_ipinfo_dispatcher() -> IPInfoDispatcher:
    global ipinfo_dispatcher

    ipinfo_dispatcher = IPInfoDispatcher()
    ipinfo_dispatcher.start()

    return ipinfo_dispatcher


def dispatch_traceroute_enrichment_job(job: EnricherJob) -> None:
    enrichment_jobs_dispatcher.queue.put(job)


def dispatch_ipinfo(ip_info: IPDBInfo) -> None:
    ipinfo_dispatcher.queue.put(ip_info)
