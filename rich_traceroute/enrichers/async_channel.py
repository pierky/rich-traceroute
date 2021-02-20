from typing import Callable, Optional
import functools
import logging

import pika

from .constants import (
    ENRICHMENT_JOBS_QUEUE_NAME,
    IP_INFO_DATA_EXCHANGE_NAME
)


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


class AsyncChannel:

    EXCHANGE_NAME: Optional[str] = None
    EXCHANGE_TYPE: Optional[str] = None

    QUEUE_NAME: Optional[str] = None
    QUEUE_ATTRIBUTES: Optional[dict] = {}

    PREFETCH_COUNT: Optional[int] = None

    PUBLISH_INTERVAL = 1

    def __init__(
        self,
        name,
        connection,
        close_connection: Callable,
        on_message: Optional[Callable] = None,
        get_message_to_publish: Optional[Callable] = None,
        # on_start_consuming: Optional[Callable] = None
    ):
        # if on_start_consuming and not on_message:
        #     raise ValueError(
        #         "on_start_consuming can be set only when "
        #         "on_message is also set."
        #     )

        self.name = name
        self.connection = connection
        self.on_message = on_message
        self.get_message_to_publish = get_message_to_publish
        self.close_connection = close_connection
        # self.on_start_consuming = on_start_consuming

        self.channel: pika.channel.Channel = None

        self._processing = False
        self._consumer_tag = None

    @property
    def is_processing(self):
        return self._processing

    def open_channel(self):
        LOGGER.debug(f"{self.name} - open_channel")

        self.connection.channel(
            on_open_callback=self._on_channel_open
        )

        LOGGER.debug(f"{self.name} - open_channel done")

    @log_exception
    def _on_channel_closed(self, channel, reason):
        LOGGER.debug(f"{self.name} - _on_channel_closed")

        LOGGER.warning(f"{self.name} - Channel {channel} was closed: {reason}")

        self.channel = None

        self.close_connection()

        LOGGER.debug(f"{self.name} - _on_channel_closed done")

    @log_exception
    def _on_channel_open(self, channel):
        LOGGER.debug(f"{self.name} - _on_channel_open")

        self.channel = channel

        self.channel.add_on_close_callback(self._on_channel_closed)

        if self.EXCHANGE_NAME:
            self._setup_exchange()

        elif self.QUEUE_NAME is not None:
            self._setup_queue()

        elif self.PREFETCH_COUNT:
            self._set_qos()

        else:
            self._start_processing()

        LOGGER.debug(f"{self.name} - _on_channel_open done")

    def _setup_exchange(self):
        LOGGER.debug(f"{self.name} - _setup_exchange")

        LOGGER.debug(f"{self.name} - Declaring exchange '{self.EXCHANGE_NAME}'")

        self.channel.exchange_declare(
            exchange=self.EXCHANGE_NAME,
            exchange_type=self.EXCHANGE_TYPE,
            callback=self._on_exchange_declare_ok
        )

        LOGGER.debug(f"{self.name} - _setup_exchange done")

    @log_exception
    def _on_exchange_declare_ok(self, _unused_frame):
        LOGGER.debug(f"{self.name} - _on_exchange_declare_ok")

        LOGGER.debug(f"{self.name} - Exchange declared")

        if self.QUEUE_NAME is not None:
            self._setup_queue()

        elif self.PREFETCH_COUNT:
            self._set_qos()

        else:
            self._start_processing()

        LOGGER.debug(f"{self.name} - _on_exchange_declare_ok done")

    def _setup_queue(self):
        LOGGER.debug(f"{self.name} - Declaring queue '{self.QUEUE_NAME}'")

        self.channel.queue_declare(
            queue=self.QUEUE_NAME,
            callback=self._on_queue_declare_ok,
            **self.QUEUE_ATTRIBUTES,
        )

    @log_exception
    def _on_queue_declare_ok(self, _unused_frame):
        LOGGER.debug(f"{self.name} - _on_queue_declare_ok")

        if self.EXCHANGE_NAME:
            LOGGER.debug(
                f"{self.name} - "
                f"Binding exchange '{self.EXCHANGE_NAME}' to "
                f"queue '{self.QUEUE_NAME}'"
            )

            self.channel.queue_bind(
                exchange=self.EXCHANGE_NAME,
                queue=self.QUEUE_NAME,
                callback=self._on_queue_bind_ok
            )

        elif self.PREFETCH_COUNT:
            self._set_qos()

        else:
            self._start_processing()

        LOGGER.debug(f"{self.name} - _on_queue_declare_ok done")

    @log_exception
    def _on_queue_bind_ok(self, _unused_frame):
        LOGGER.debug(f"{self.name} - _on_queue_bind_ok")

        LOGGER.debug(f"{self.name} - Queue bound")

        if self.PREFETCH_COUNT:
            self._set_qos()

        else:
            self._start_processing()

        LOGGER.debug(f"{self.name} - _on_queue_bind_ok")

    def _set_qos(self):
        self.channel.basic_qos(
            prefetch_count=self.PREFETCH_COUNT,
            callback=self._on_basic_qos_ok
        )

    @log_exception
    def _on_basic_qos_ok(self, _unused_frame):
        LOGGER.debug(f"{self.name} - _on_basic_qos_ok")

        LOGGER.debug(f"{self.name} - QOS set to: {self.PREFETCH_COUNT}")
        self._start_processing()

        LOGGER.debug(f"{self.name} - _on_basic_qos_ok done")

    def _start_processing(self):
        LOGGER.debug(f"{self.name} - _start_processing")

        if self.on_message:
            LOGGER.debug(f"{self.name} - Issuing consumer related RPC commands")

            self.channel.add_on_cancel_callback(
                self._on_consumer_cancelled
            )

            self._consumer_tag = self.channel.basic_consume(
                self.QUEUE_NAME,
                self.on_message
            )
            self._processing = True

            # if self.on_start_consuming:
            #     self.on_start_consuming()

        if self.get_message_to_publish:
            self.connection.ioloop.call_later(
                self.PUBLISH_INTERVAL,
                self._on_ready_to_publish_message
            )

        LOGGER.debug(f"{self.name} - _start_processing done")

    @log_exception
    def _on_ready_to_publish_message(self):
        if self.channel is None or not self.channel.is_open:
            LOGGER.debug(f"{self.name} - _on_ready_to_publish_message aborted: channel is closed")
            return

        msg = self.get_message_to_publish()

        while msg:
            LOGGER.debug(f"{self.name} - publishing message")
            self.channel.basic_publish(
                exchange=self.EXCHANGE_NAME,
                routing_key=self.QUEUE_NAME,
                body=msg,
                properties=pika.BasicProperties(
                    expiration='120000',
                )
            )

            msg = self.get_message_to_publish()

        self.connection.ioloop.call_later(
            self.PUBLISH_INTERVAL,
            self._on_ready_to_publish_message
        )

    @log_exception
    def _on_consumer_cancelled(self, method_frame):
        LOGGER.debug(f"{self.name} - _on_consumer_cancelled")

        LOGGER.debug(f"{self.name} - Consumer was cancelled remotely, "
                     f"shutting down: {method_frame}")

        if self.channel:
            self.channel.close()

        LOGGER.debug(f"{self.name} - _on_consumer_cancelled done")

    def stop_processing(self):
        if self.channel:
            LOGGER.debug(f"{self.name} - Sending a Basic.Cancel RPC command to RabbitMQ")

            self.channel.basic_cancel(
                self._consumer_tag,
                self._on_cancel_ok
            )

    @log_exception
    def _on_cancel_ok(self, _unused_frame_):
        LOGGER.debug(f"{self.name} - on_cancelok_")

        self._processing = False

        LOGGER.debug(
            f"{self.name} - "
            "RabbitMQ acknowledged the cancellation "
            f"of the consumer: {self._consumer_tag}"
        )

        self.close_channel()

        LOGGER.debug(f"{self.name} - on_cancelok done_")

    def close_channel(self):
        LOGGER.debug(f"{self.name} - Closing the channel")
        self.channel.close()


class EnrichmentJobsChannel(AsyncChannel):

    QUEUE_NAME = ENRICHMENT_JOBS_QUEUE_NAME

    QUEUE_ATTRIBUTES = {
        "passive": False,
        "durable": False,
        "exclusive": False,
        "auto_delete": False
    }

    PREFETCH_COUNT = 1


class IPDBInfoChannel(AsyncChannel):

    QUEUE_NAME = ""

    EXCHANGE_NAME = IP_INFO_DATA_EXCHANGE_NAME
    EXCHANGE_TYPE = "fanout"

    QUEUE_ATTRIBUTES = {
        "exclusive": True
    }

    PREFETCH_COUNT = 10


class TracerouteDispatcherChannel(AsyncChannel):

    QUEUE_NAME = ENRICHMENT_JOBS_QUEUE_NAME

    EXCHANGE_NAME = ""

    QUEUE_ATTRIBUTES = {
        "passive": False,
        "durable": False,
        "exclusive": False,
        "auto_delete": False
    }
