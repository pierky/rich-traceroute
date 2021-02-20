from typing import Union, Optional, List
import ipaddress
import os
import hashlib
import json
import random
import string

import pytest
from markus.testing import MetricsMock

from rich_traceroute.db import (
    connect_to_the_db,
    disconnect_from_the_db
)
from rich_traceroute.enrichers.consumer import setup_consumers
from rich_traceroute.enrichers.dispatcher import (
    setup_enrichment_jobs_dispatcher,
    setup_ipinfo_dispatcher
)
from rich_traceroute.enrichers.ixp_networks import IXPNetworksUpdater
from rich_traceroute.logging_config import configure_logging
from rich_traceroute.config import load_config
from rich_traceroute.metrics import configure_metrics

from .docker_rabbitmq import RABBIT_MQ_CONTAINER
from .docker_mysql import MYSQL_CONTAINER


# Will be used by tests to access the consumer threads.
# Please note: do not set this variable from within
# fixtures, but rather just add/remove threads are they
# are spun up or destroyed. If the variable gets reset,
# the test cases in other modules will loose access to
# it.
CONSUMER_THREADS: List = []
CONSUMER_THREADS_NUM = 3


# Wrapper for the markus MetricsMock singleton that
# is used by test cases to verify interaction with
# the metrics backend.
# The singleton metrics_mock_wrapper is instantiated
# at module level here, and imported by test modules;
# as soon as the markus object is setup, its internal
# attribute metrics_mock is set. This allows test
# modules to load a de-facto uninitialised wrapper
# and still be able to consume its internal actual
# MetricsMock object later on.
class MetricsMockWrapper:

    def __init__(self):
        self.metrics_mock: MetricsMock

    def set_metrics_mock(self, metrics_mock: MetricsMock) -> None:
        self.metrics_mock = metrics_mock

    @property
    def mm(self):
        return self.metrics_mock


metrics_mock_wrapper = MetricsMockWrapper()


@pytest.fixture()
def db(tmpdir, mocker):

    def _fake_get_db_type_sqlite(*args):
        return "sqlite"

    def _fake_get_db_type_mysql(*args):
        return "mysql"

    def _fake_get_db_path(*args):
        return db_path

    def _fake_get_db_init_args(*args):
        return (
            random_schema,
            "127.0.0.1",
            3306,
            "root",
            "",
        )

    db_type = os.environ.get("RICH_TRACEROUTE_TESTS_DB_TYPE", "sqlite")

    if db_type == "sqlite":
        db_dir = tmpdir.mkdir("db")
        db_path = db_dir.join("test.db")
        print(str(db_path) + " ", end="")

        mocker.patch("rich_traceroute.db._get_db_type", _fake_get_db_type_sqlite)
    elif db_type == "mysql":
        random_schema = ''.join(
            random.choice(
                string.ascii_uppercase + string.digits
            ) for _ in range(10)
        )
        print(random_schema + " ", end="")

        MYSQL_CONTAINER.ensure_is_up()
        MYSQL_CONTAINER.init_schema(random_schema)

        mocker.patch("rich_traceroute.db._get_db_type", _fake_get_db_type_mysql)
    else:
        raise ValueError(f"Unknown value of RICH_TRACEROUTE_TESTS_DB_TYPE: {db_type}")

    mocker.patch("rich_traceroute.db._get_db_path", _fake_get_db_path)
    mocker.patch("rich_traceroute.db._get_db_init_args", _fake_get_db_init_args)

    connect_to_the_db()

    yield

    disconnect_from_the_db()


@pytest.fixture()
def rabbitmq():
    RABBIT_MQ_CONTAINER.ensure_is_up()

    tr_dispatcher_thread = setup_enrichment_jobs_dispatcher()
    ipinfo_thread = setup_ipinfo_dispatcher()

    for thread in setup_consumers(consumers=3, enrichers_per_consumer=3):
        CONSUMER_THREADS.append(thread)

    yield

    tr_dispatcher_thread.stop_dispatcher()
    ipinfo_thread.stop_dispatcher()

    for thread in CONSUMER_THREADS:
        thread.stop_consumer()

    for thread in CONSUMER_THREADS:
        thread.join()

    del CONSUMER_THREADS[:]


@pytest.fixture(autouse=True, scope="session")
def config():

    load_config("tests/data/config.yml")

    yield


@pytest.fixture(autouse=True, scope="session")
def logging_setup(config):

    configure_logging()

    yield


@pytest.fixture(autouse=True, scope="session")
def metrics_setup():
    global metrics_mock

    configure_metrics()

    with MetricsMock() as mm:
        metrics_mock_wrapper.set_metrics_mock(mm)
        yield


@pytest.fixture()
def ixp_networks(db, rabbitmq):
    updater = IXPNetworksUpdater()
    updater.update_ixp_networks()

    yield


@pytest.fixture(autouse=True)
def external_resources(mocker):

    # IP/hostname resolution
    # ----------------------

    @staticmethod
    def fake_get_hostname_from_ip(
        ip: Union[ipaddress.IPv4Network, ipaddress.IPv6Network]
    ) -> Optional[str]:
        ip_str = str(ip)

        path = os.path.join("tests", "data", "host_from_ip", ip_str + ".txt")

        if not os.path.exists(path):
            raise ValueError(
                f"_get_hostname_from_ip, value not found for {ip_str}.\n"
                "To gather it and store it for testing purposes:\n"
                f"  dig +short -x {ip_str} > {path}"
            )

        with open(path, "r") as f:
            res = f.read()

        if res:
            res = res.strip()

        if res.endswith("."):
            res = res[:-1]

        if res:
            return res
        else:
            return None

    @staticmethod
    def fake_get_ip_from_hostname(fqdn: str) -> Optional[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]]:
        path = os.path.join("tests", "data", "ip_from_host", fqdn + ".txt")

        if not os.path.exists(path):
            raise ValueError(
                f"_get_ip_from_hostname, value not found for {fqdn}.\n"
                "To gather it and store it for testing purposes:\n"
                f"  dig +short {fqdn} | head -n 1 > {path}"
            )

        with open(path, "r") as f:
            res = f.read()

        if res:
            res = res.strip()

        if res:
            return ipaddress.ip_address(res)
        else:
            return None

    mocker.patch(
        "rich_traceroute.enrichers.enricher.Enricher._get_hostname_from_ip",
        fake_get_hostname_from_ip
    )
    mocker.patch(
        "rich_traceroute.enrichers.enricher.Enricher._get_ip_from_hostname",
        fake_get_ip_from_hostname
    )

    # requests.get
    # ------------

    class FakeRequestResponse:

        def __init__(self, url: str):
            m = hashlib.sha1()
            m.update(url.encode())
            url_hash = m.hexdigest()

            path = os.path.join(
                "tests",
                "data",
                "requests.get",
                url_hash + ".txt"
            )

            if not os.path.exists(path):
                raise ValueError(
                    f"requests.get, value not found for {url}.\n"
                    "To gather it and store it for testing purposes:\n"
                    f"  curl -o {path} {url}"
                )

            with open(path, "r") as f:
                self.data = f.read()

        def raise_for_status(self):
            pass

        def json(self):
            return json.loads(self.data)

    def fake_requests_get(url) -> FakeRequestResponse:
        return FakeRequestResponse(url)

    def fake_ripe_stat_query(self, url) -> FakeRequestResponse:
        return FakeRequestResponse(url)

    def fake_peeringdb_get(self, url) -> FakeRequestResponse:
        return FakeRequestResponse(url)

    mocker.patch(
        "requests.get",
        fake_requests_get
    )
    mocker.patch(
        "rich_traceroute.enrichers.enricher.Enricher._ripe_stat_query",
        fake_ripe_stat_query
    )
    mocker.patch(
        "rich_traceroute.enrichers.ixp_networks.PeeringDB._get",
        fake_peeringdb_get
    )

    yield
