from typing import Optional
import os
import threading
import socket
import logging
from contextlib import ContextDecorator
import time

import markus
from markus.utils import generate_tag


from .config import get_markus_options


def configure_metrics():
    markus.configure(
        backends=get_markus_options()
    )


def get_tags():
    return [
        generate_tag("hostname", socket.gethostname()),
        generate_tag("pid", str(os.getpid())),
        generate_tag("thread_id", threading.current_thread().name),
    ]


class log_execution_time(ContextDecorator):

    def __init__(
        self,
        markus_metrics: markus.main.MetricsInterface,
        logger: logging.Logger,
        metric: str,
        descr: Optional[str] = None
    ):
        self.markus_metrics = markus_metrics
        self.logger = logger
        self.metric = metric
        self.descr = descr

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, type, value, traceback):
        self.stop = time.perf_counter()

        duration = round(1000 * (self.stop - self.start))

        log_msg = f"Timing of {self.metric}"

        if self.descr:
            log_msg += f" {self.descr}"

        log_msg += f" - {duration} ms"

        self.logger.debug(log_msg)

        self.markus_metrics.timing(self.metric, duration, get_tags())
