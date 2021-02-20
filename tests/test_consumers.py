from typing import List, Tuple, Optional
import ipaddress
from unittest.mock import MagicMock
import time
import os

import pytest

from rich_traceroute.traceroute import (
    create_traceroute,
    Traceroute
)
from rich_traceroute.ip_info_db import IPInfo_Prefix
from rich_traceroute.structures import IPDBInfo, IXPNetwork
from rich_traceroute.config import (
    SOCKET_IO_DATA_EVENT,
    SOCKET_IO_ENRICHMENT_COMPLETED_EVENT,
)

from .docker_rabbitmq import RABBIT_MQ_CONTAINER
from .docker_mysql import MYSQL_CONTAINER
from .conftest import (
    CONSUMER_THREADS,
    CONSUMER_THREADS_NUM,
    metrics_mock_wrapper
)

# Will be set by the fixture and made available to the
# test case function for inspection.
socketio_emit_mock: MagicMock


# List of expected SocketIO.emit calls for the test
# traceroute 1.json.
EXPECTED_SOCKETIO_EMIT_CALLS_TR1 = [
    # host_ip, host_name, ip_info
    ("192.168.1.254", None, None, None),
    ("10.1.131.181", None, None, None),
    ("10.250.139.186", None, None, None),
    ("10.254.0.217", None, None, None),
    ("89.97.200.190", None,
     [(12874, "FASTWEB - Fastweb SpA")],
     None),
    ("62.101.124.17", "62-101-124-17.fastres.net",
     [(12874, "FASTWEB - Fastweb SpA")],
     None),
    ("209.85.168.64", None,
     [(15169, "GOOGLE")],
     None),
    ("216.239.51.9", None,
     [(15169, "GOOGLE")],
     None),
    ("216.239.50.241", None,
     [(15169, "GOOGLE")],
     None),
    ("8.8.8.8", "dns.google",
     [(15169, "GOOGLE")],
     None)
]
# List of expected SocketIO.emit calls for the test
# traceroute 1.json.
EXPECTED_SOCKETIO_EMIT_CALLS_TR2 = [
    # host_ip, host_name, ip_info
    ("192.168.1.254", None, None, None),
    ("10.1.131.181", None, None, None),
    ("10.250.139.190", None, None, None),
    ("10.254.0.221", None, None, None),
    ("89.97.200.201", None,
     [(12874, "FASTWEB - Fastweb SpA")],
     None),
    ("93.63.100.141", "93-63-100-141.ip27.fastwebnet.it",
     [(12874, "FASTWEB - Fastweb SpA")],
     None),
    ("217.29.66.1", "mix-1.mix-it.net",
     None, {
         "lan_name": None,
         "ix_name": "MIX-IT",
         "ix_description": "Milan Internet eXchange"
     }),
    ("217.29.76.16", "kroot-server1.mix-it.net",
     [(16004, "MIXITA-AS - MIX S.r.L. - Milan Internet eXchange")],
     None)
]


def _prefix_traceroute_id(
    base_expectations: List[Tuple[str, Optional[str], Optional[dict]]],
    traceroute_id: str
) -> List[Tuple[str, str, Optional[str], Optional[dict]]]:
    """Add traceroute_id as the first item of tuples from EXPECTED_SOCKETIO_EMIT_CALLS_TR*."""
    res = []
    for t in base_expectations:
        res.append((traceroute_id,) + t)

    return res


def _get_socketio_emitted_records() -> List[Tuple]:
    """Get a simplified version of calls from socketio_emit_mock."""
    return [
        (
            call[0][1]["traceroute_id"],
            call[0][1]["ip"],
            call[0][1]["name"],
            call[0][1]["origins"],
            call[0][1]["ixp_network"],
        )
        for call in socketio_emit_mock.call_args_list
        if call[0][0] == SOCKET_IO_DATA_EVENT
    ]


@pytest.fixture(autouse=True)
def mock_env(db, rabbitmq):
    yield


@pytest.fixture(autouse=True)
def socketio(mocker):
    global socketio_emit_mock

    socketio_emit_mock = MagicMock()

    mocker.patch(
        "rich_traceroute.enrichers.enricher.SocketIO.emit",
        socketio_emit_mock
    )


def _wait_for_completion():
    time.sleep(10)


def test_consumers_basic():
    """
    Create a traceroute and get it parsed and enriched
    using consumers.
    """

    # Just to be sure that we're actually using the
    # n. of thread we expect, just in case I'll change
    # the way consumer threads are spun up while doing
    # some debugging.
    assert CONSUMER_THREADS_NUM > 1
    assert len(CONSUMER_THREADS) == CONSUMER_THREADS_NUM

    raw = open("tests/data/traceroute/mtr_json_1.json").read()
    t_id = create_traceroute(raw).id

    _wait_for_completion()

    # Compare the SocketIO records emitted by the enricher
    # with those that we expect to see.
    socketio_emitted_records = _get_socketio_emitted_records()

    expected_socketio_emitted_records = _prefix_traceroute_id(
        EXPECTED_SOCKETIO_EMIT_CALLS_TR1,
        t_id
    )

    assert socketio_emitted_records == expected_socketio_emitted_records

    # Verify that the last call to SocketIO is the one
    # that notifies about the completion of the
    # enrichment process.
    t = Traceroute.select()[0]
    socketio_emit_mock.assert_called_with(
        SOCKET_IO_ENRICHMENT_COMPLETED_EVENT,
        {
            "traceroute_id": t_id,
            "text": t.to_text()
        },
        namespace=f"/t/{t_id}"
    )

    # Let's check that the traceroute is in the expected
    # state, and that hops and hosts were processed.
    t = Traceroute.select()[0]

    assert t.parsed is True
    assert t.enriched is True

    assert len(t.hops) == 10

    hop = t.get_hop_n(1)
    assert len(hop.hosts) == 1
    host = hop.hosts[0]
    assert host.original_host == "192.168.1.254"
    assert str(host.ip) == "192.168.1.254"
    assert host.name is None
    assert host.enriched is True
    assert len(host.origins) == 0
    assert host.ixp_network is None

    hop = t.get_hop_n(6)
    assert len(hop.hosts) == 1
    host = hop.hosts[0]
    assert host.original_host == "62-101-124-17.fastres.net"
    assert str(host.ip) == "62.101.124.17"
    assert host.name == "62-101-124-17.fastres.net"
    assert host.enriched is True
    assert len(host.origins) == 1
    origin = host.origins[0]
    assert origin.asn == 12874
    assert origin.holder == "FASTWEB - Fastweb SpA"
    assert host.ixp_network is None

    hop = t.get_hop_n(10)
    assert len(hop.hosts) == 1
    host = hop.hosts[0]
    assert host.original_host == "dns.google"
    assert str(host.ip) == "8.8.8.8"
    assert host.name == "dns.google"
    assert host.enriched is True
    assert len(host.origins) == 1
    origin = host.origins[0]
    assert origin.asn == 15169
    assert origin.holder == "GOOGLE"
    assert host.ixp_network is None

    # Now, let's verify that all the enrichers from
    # the consumer threads got their IP info DB populated
    # equally. This is to ensure that the IP info records
    # are properly distributed across the consumers.
    for thread in CONSUMER_THREADS:
        for enricher in thread.enrichers:
            ip_info_db = enricher.ip_info_db

            assert len(ip_info_db.nodes()) == 5

            assert sorted(ip_info_db.prefixes()) == sorted([
                "89.97.0.0/16",
                "62.101.124.0/22",
                "209.85.128.0/17",
                "216.239.32.0/19",
                "8.8.8.0/24",
            ])

            assert ip_info_db.search_exact(
                "89.97.0.0/16"
            ).data["ip_db_info"] == IPDBInfo(
                prefix=ipaddress.ip_network("89.97.0.0/16"),
                origins=[
                    (12874, "FASTWEB - Fastweb SpA")
                ],
                ixp_network=None
            )

    # Check now that the IP Info DB is populated properly.
    db_prefixes = IPInfo_Prefix.select()

    # Build a dict using DB records to make comparisons easier.
    db_prefixes_dict = {
        db_prefix.prefix: db_prefix.origins
        for db_prefix in db_prefixes
    }

    assert len(db_prefixes_dict.keys()) == 5

    assert sorted(db_prefixes_dict.keys()) == sorted([
        ipaddress.IPv4Network("89.97.0.0/16"),
        ipaddress.IPv4Network("62.101.124.0/22"),
        ipaddress.IPv4Network("209.85.128.0/17"),
        ipaddress.IPv4Network("216.239.32.0/19"),
        ipaddress.IPv4Network("8.8.8.0/24")
    ])

    db_prefix = IPInfo_Prefix.get(prefix="89.97.0.0/16")
    assert db_prefix.to_ipdbinfo() == IPDBInfo(
        prefix=ipaddress.ip_network("89.97.0.0/16"),
        origins=[
            (12874, "FASTWEB - Fastweb SpA")
        ],
        ixp_network=None
    )

    # Verify that metrics logging is working properly.
    # To see which metrics have been collected:
    #   metrics_mock_wrapper.mm.print_records()

    mm_records = metrics_mock_wrapper.mm.get_records()

    # Expecting 5 calls to the function that performs
    # external queries to fetch IP info.
    # Every time, we want the counter to be increased.
    mm_ip_info_from_external_sources = filter(
        lambda r: (
            r[0] == "incr" and
            r[1] == ("rich_traceroute.enrichers.enricher."
                     "ip_info_from_external_sources") and
            r[2] == 1
        ),
        mm_records
    )
    assert len(list(mm_ip_info_from_external_sources)) == 5

    # Check that we're keeping track of how long those
    # 5 upstream queries take to complete.
    mm_ip_info_from_external_sources = filter(
        lambda r: (
            r[0] == "timing" and
            r[1] == ("rich_traceroute.enrichers.enricher."
                     "ripestat.query_time")
        ),
        mm_records
    )
    assert len(list(mm_ip_info_from_external_sources)) == 5


def test_consumers_update():
    """
    Create a traceroute and get it parsed and enriched
    using consumers, then shut RabbitMQ down and spin
    it up again, and process another traceroute, to test
    that consumers are actually able to reconnect to the
    RabbitMQ server properly if it goes down and comes
    back.
    """

    assert len(CONSUMER_THREADS) == CONSUMER_THREADS_NUM

    raw = open("tests/data/traceroute/mtr_json_1.json").read()
    t1_id = create_traceroute(raw).id

    _wait_for_completion()

    # Compare the SocketIO records emitted by the enricher
    # with those that we expect to see.
    socketio_emitted_records = _get_socketio_emitted_records()

    expected_socketio_emitted_records = _prefix_traceroute_id(
        EXPECTED_SOCKETIO_EMIT_CALLS_TR1,
        t1_id
    )

    assert socketio_emitted_records == expected_socketio_emitted_records

    # Verify that the last call to SocketIO is the one
    # that notifies about the completion of the
    # enrichment process.
    t = Traceroute.get(Traceroute.id == t1_id)
    socketio_emit_mock.assert_called_with(
        SOCKET_IO_ENRICHMENT_COMPLETED_EVENT,
        {
            "traceroute_id": t1_id,
            "text": t.to_text()
        },
        namespace=f"/t/{t1_id}"
    )

    t = Traceroute.get(Traceroute.id == t1_id)

    assert t.parsed is True
    assert t.enriched is True

    RABBIT_MQ_CONTAINER.kill_existing_container()

    RABBIT_MQ_CONTAINER.ensure_is_up()

    raw = open("tests/data/traceroute/mtr_json_1.json").read()
    t2_id = create_traceroute(raw).id

    _wait_for_completion()

    # At this point, the records emitted via SocketIO
    # should be those originated while parsing the first
    # traceroute + those originated while parsing the
    # second one.
    socketio_emitted_records = _get_socketio_emitted_records()

    expected_socketio_emitted_records = \
        _prefix_traceroute_id(EXPECTED_SOCKETIO_EMIT_CALLS_TR1, t1_id) + \
        _prefix_traceroute_id(EXPECTED_SOCKETIO_EMIT_CALLS_TR1, t2_id)

    assert socketio_emitted_records == expected_socketio_emitted_records

    t = Traceroute.get(Traceroute.id == t2_id)

    assert t.parsed is True
    assert t.enriched is True

    assert len(CONSUMER_THREADS) == CONSUMER_THREADS_NUM


def test_ixp_networks_updater_integration(ixp_networks):
    """
    Process a traceroute having some hops crossing an IXP network.
    """

    raw = open("tests/data/traceroute/mtr_json_2.json").read()
    t1_id = create_traceroute(raw).id

    _wait_for_completion()

    # Compare the SocketIO records emitted by the enricher
    # with those that we expect to see.
    socketio_emitted_records = _get_socketio_emitted_records()

    expected_socketio_emitted_records = _prefix_traceroute_id(
        EXPECTED_SOCKETIO_EMIT_CALLS_TR2,
        t1_id
    )

    assert socketio_emitted_records == expected_socketio_emitted_records

    # Verify that the last call to SocketIO is the one
    # that notifies about the completion of the
    # enrichment process.
    t = Traceroute.get(Traceroute.id == t1_id)
    socketio_emit_mock.assert_called_with(
        SOCKET_IO_ENRICHMENT_COMPLETED_EVENT,
        {
            "traceroute_id": t1_id,
            "text": t.to_text()
        },
        namespace=f"/t/{t1_id}"
    )

    t = Traceroute.get(Traceroute.id == t1_id)

    assert t.parsed is True
    assert t.enriched is True

    assert len(t.hops) == 8

    # Check that the host inside the IXP network is correct.
    hop = t.get_hop_n(7)
    assert len(hop.hosts) == 1
    host = hop.hosts[0]
    assert host.original_host == "217.29.66.1"
    assert str(host.ip) == "217.29.66.1"
    assert host.name == "mix-1.mix-it.net"
    assert host.enriched is True
    assert len(host.origins) == 0
    assert host.ixp_network is not None
    assert host.ixp_network.lan_name is None
    assert host.ixp_network.ix_name == "MIX-IT"
    assert host.ixp_network.ix_description == "Milan Internet eXchange"

    # Now, let's verify that all the enrichers from
    # the consumer threads got their IP info DB populated
    # equally. This is to ensure that the IXPNetworksUpdater
    # properly dispatch the IP info entries to all the
    # consumers.
    for thread in CONSUMER_THREADS:
        for enricher in thread.enrichers:

            ip_info_db = enricher.ip_info_db

            assert len(ip_info_db.nodes()) == 4

            assert sorted(ip_info_db.prefixes()) == sorted([
                "89.97.0.0/16",
                "93.62.0.0/15",
                "217.29.66.0/23",
                "217.29.72.0/21"
            ])

            assert ip_info_db.search_exact(
                "217.29.66.0/23"
            ).data["ip_db_info"] == IPDBInfo(
                prefix=ipaddress.ip_network("217.29.66.0/23"),
                origins=None,
                ixp_network=IXPNetwork(
                    lan_name=None,
                    ix_name="MIX-IT",
                    ix_description="Milan Internet eXchange"
                )
            )

    # Check now that the IP Info DB is populated properly.
    db_prefixes = IPInfo_Prefix.select()

    # Build a dict using DB records to make comparisons easier.
    db_prefixes_dict = {
        db_prefix.prefix: db_prefix.origins
        for db_prefix in db_prefixes
    }

    assert len(db_prefixes_dict.keys()) == 4

    assert sorted(db_prefixes_dict.keys()) == sorted([
        ipaddress.IPv4Network("89.97.0.0/16"),
        ipaddress.IPv4Network("93.62.0.0/15"),
        ipaddress.IPv4Network("217.29.66.0/23"),
        ipaddress.IPv4Network("217.29.72.0/21"),
    ])

    db_prefix = IPInfo_Prefix.get(prefix="217.29.66.0/23")
    assert db_prefix.to_ipdbinfo() == IPDBInfo(
        prefix=ipaddress.ip_network("217.29.66.0/23"),
        origins=None,
        ixp_network=IXPNetwork(
            lan_name=None,
            ix_name="MIX-IT",
            ix_description="Milan Internet eXchange"
        )
    )


@pytest.mark.skipif(
    os.environ.get("RICH_TRACEROUTE_TESTS_DB_TYPE", "") != "mysql",
    reason="Only possible when the backend used for the test is MySQL"
)
def test_consumers_mysql_goes_away():
    """
    Create a traceroute and get it parsed and enriched
    using consumers, then shut MySQL down and spin
    it up again, and process another traceroute, to test
    that consumers are actually able to reconnect to the
    DB server properly if it goes down and comes back.
    """

    assert len(CONSUMER_THREADS) == CONSUMER_THREADS_NUM

    raw = open("tests/data/traceroute/mtr_json_1.json").read()
    t1_id = create_traceroute(raw).id

    _wait_for_completion()

    # Compare the SocketIO records emitted by the enricher
    # with those that we expect to see.
    socketio_emitted_records = _get_socketio_emitted_records()

    expected_socketio_emitted_records = _prefix_traceroute_id(
        EXPECTED_SOCKETIO_EMIT_CALLS_TR1,
        t1_id
    )

    assert socketio_emitted_records == expected_socketio_emitted_records

    # Verify that the last call to SocketIO is the one
    # that notifies about the completion of the
    # enrichment process.
    t = Traceroute.get(Traceroute.id == t1_id)
    socketio_emit_mock.assert_called_with(
        SOCKET_IO_ENRICHMENT_COMPLETED_EVENT,
        {
            "traceroute_id": t1_id,
            "text": t.to_text()
        },
        namespace=f"/t/{t1_id}"
    )

    t = Traceroute.get(Traceroute.id == t1_id)

    assert t.parsed is True
    assert t.enriched is True

    MYSQL_CONTAINER.kill_existing_container()

    MYSQL_CONTAINER.ensure_is_up()
    MYSQL_CONTAINER.recreate_last_schema()

    raw = open("tests/data/traceroute/mtr_json_1.json").read()
    t2_id = create_traceroute(raw).id

    _wait_for_completion()

    # At this point, the records emitted via SocketIO
    # should be those originated while parsing the first
    # traceroute + those originated while parsing the
    # second one.
    socketio_emitted_records = _get_socketio_emitted_records()

    expected_socketio_emitted_records = \
        _prefix_traceroute_id(EXPECTED_SOCKETIO_EMIT_CALLS_TR1, t1_id) + \
        _prefix_traceroute_id(EXPECTED_SOCKETIO_EMIT_CALLS_TR1, t2_id)

    assert socketio_emitted_records == expected_socketio_emitted_records

    t = Traceroute.get(Traceroute.id == t2_id)

    assert t.parsed is True
    assert t.enriched is True

    assert len(CONSUMER_THREADS) == CONSUMER_THREADS_NUM
