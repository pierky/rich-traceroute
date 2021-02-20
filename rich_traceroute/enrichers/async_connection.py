from typing import List, Type
import logging
import functools
import time

import pika


from .async_channel import AsyncChannel
from ..config import get_pika_url_parameters

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


class AsyncConnection:

    def __init__(self):

        self._closing = False
        self.should_reconnect = False

        self.connection: pika.SelectConnection = None
        self._channels: List[AsyncChannel] = []

    def close_connection(self):
        if self.connection.is_closing:
            LOGGER.debug('Connection is already closing')
        elif self.connection.is_closed:
            LOGGER.debug('Connection is already closed')
        else:
            LOGGER.debug('Closing connection')
            self.connection.close()

    @log_exception
    def on_connection_open_error(self, _unused_connection, err):
        LOGGER.error(f'Connection open failed: {err}')
        self.reconnect()

    @log_exception
    def on_connection_closed(self, _unused_connection, reason):
        if self._closing:
            self.connection.ioloop.stop()
        else:
            LOGGER.warning(f'Connection closed, reconnect necessary: {reason}')
            self.reconnect()

    def reconnect(self):
        self.should_reconnect = True
        self.stop()

    @log_exception
    def on_connection_open(self, _unused_connection):
        LOGGER.debug("on_connection_open")

        self._setup_channels()

        for async_channel in self._channels:
            async_channel.open_channel()

        LOGGER.debug("on_connection_open done")

    def stop(self):
        if not self._closing:
            self._closing = True

            LOGGER.info('Stopping')

            for async_channel in self._channels:
                if async_channel.is_processing:
                    async_channel.stop_processing()

            self.connection.ioloop.stop()

            LOGGER.info('Stopped')

    def connect(self):
        self.connection = pika.SelectConnection(
            get_pika_url_parameters(),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed
        )

    def _setup_channels(self):
        raise NotImplementedError()

    def run(self):
        LOGGER.info("Consumer starting up.")
        self.connect()
        self.connection.ioloop.start()
        LOGGER.info("Consumer completed.")


class Reconnector:

    def __init__(self, async_connection_class: Type[AsyncConnection], *args):
        self.async_connection_class = async_connection_class
        self.async_connection_args = args
        self._reconnect_delay = 0

        self.async_connection: AsyncConnection
        self._setup_async_connection()

    def _setup_async_connection(self):
        self.async_connection = self.async_connection_class(*self.async_connection_args)

    def run(self):
        while True:
            try:
                LOGGER.info("Reconnector self.async_connection.run()")
                self.async_connection.run()
                LOGGER.info("Reconnector self.async_connection.run() DONE")
            except KeyboardInterrupt:
                self.async_connection.stop()
                break

            if not self._maybe_reconnect():
                return

    def _maybe_reconnect(self) -> bool:
        if self.async_connection.should_reconnect:
            LOGGER.info("Reconnector attempting reconnection")
            self.async_connection.stop()
            reconnect_delay = self._get_reconnect_delay()
            LOGGER.info('Reconnector - Reconnecting after %d seconds', reconnect_delay)
            time.sleep(reconnect_delay)
            self._setup_async_connection()
            return True

        return False

    def _get_reconnect_delay(self):
        self._reconnect_delay += 1
        if self._reconnect_delay > 30:
            self._reconnect_delay = 30
        return self._reconnect_delay

    def stop(self):
        self.async_connection.stop()
