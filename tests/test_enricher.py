import pytest
from unittest.mock import MagicMock, call
from ipaddress import IPv4Address, IPv4Network
import datetime

from rich_traceroute.traceroute import (
    create_traceroute,
    Traceroute
)
from rich_traceroute.enrichers.enricher import Enricher
from rich_traceroute.structures import EnricherJob, IPDBInfo, IXPNetwork


# Will be set by the fixture and made available to the
# test case function for inspection.
get_ip_info_from_external_sources_mock = None
enricher: Enricher


@pytest.fixture(autouse=True)
def prevent_any_rabbitmq_connection(db, mocker):

    _setup_enricher(mocker)


def _setup_enricher(mocker):
    global enricher

    enricher = Enricher("enricher-1", None)

    def process_job_locally(job: EnricherJob) -> None:
        enricher.process_traceroute_enrichment_job(job)

    mocker.patch("rich_traceroute.traceroute.dispatch_traceroute_enrichment_job", process_job_locally)

    global get_ip_info_from_external_sources_mock
    get_ip_info_from_external_sources_mock = MagicMock(
        enricher._get_ip_info_from_external_sources,
        wraps=enricher._get_ip_info_from_external_sources
    )

    enricher._get_ip_info_from_external_sources = get_ip_info_from_external_sources_mock

    # Avoid dispatching IPInfo to others.
    def fake_dispatch_ipinfo(*args, **kwargs):
        pass

    mocker.patch("rich_traceroute.enrichers.enricher.dispatch_ipinfo", fake_dispatch_ipinfo)

    # To prevent the enricher from being blocked if there
    # is no RabbitMQ availability, for example when the
    # test case is executed alone without bringing up the
    # docker container.
    def socketio_emit(*args, **kwargs):
        pass

    mocker.patch(
        "rich_traceroute.enrichers.enricher.SocketIO.emit",
        socketio_emit
    )

    # To simulate the thread startup, I'm invoking
    # the _load_ip_info_entries_from_db method of the enricher
    # instance here: this would normally happen as soon as
    # the enricher thread runs.
    enricher._load_ip_info_entries_from_db()


def test_enricher_basic():
    raw = open("tests/data/traceroute/mtr_json_1.json").read()
    create_traceroute(raw)

    # Verify the calls to the function that's used to
    # retrieve IP information from external sources.

    # Please note: a call for hop 9 IP 216.239.50.241 should not
    # be performed because an entry for 216.239.32.0/19 should
    # be found while getting IPDBInfo for 216.239.51.9
    assert get_ip_info_from_external_sources_mock.call_args_list == [
        call(IPv4Address("89.97.200.190")),
        call(IPv4Address("62.101.124.17")),      # 62-101-124-17.fastres.net
        call(IPv4Address("209.85.168.64")),
        call(IPv4Address("216.239.51.9")),
        # call(IPv4Address("216.239.50.241")), <<< expected to be missing
        call(IPv4Address("8.8.8.8"))
    ]

    # Verify that the traceroute is marked as parsed
    # and enriched properly.

    t = Traceroute.select()[0]

    assert t.parsed is True
    assert t.enriched is True
    assert t.enrichment_started is not None
    assert t.enrichment_completed is not None
    assert t.enrichment_completed >= t.enrichment_started

    assert len(t.hops) == 10

    hop = t.get_hop_n(1)
    assert len(hop.hosts) == 1
    host = hop.hosts[0]
    assert host.original_host == "192.168.1.254"
    assert str(host.ip) == "192.168.1.254"
    assert host.name is None
    assert host.enriched is True
    assert len(host.origins) == 0

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

    # Verify the to_dict of Traceroute.
    json_t = t.to_dict()

    assert json_t["enriched"] is True
    assert json_t["status"] == "enriched"
    assert len(json_t["hops"]) == 10

    json_host = json_t["hops"][1][0]
    assert json_host["ip"] == "192.168.1.254"
    assert json_host["ixp_network"] is None
    assert json_host["origins"] is None
    assert isinstance(json_host["avg_rtt"], float)
    assert isinstance(json_host["loss"], float)
    assert json_host["loss"] == 0

    json_host = json_t["hops"][10][0]
    assert json_host["ip"] == "8.8.8.8"
    assert json_host["ixp_network"] is None
    assert json_host["origins"] == [
        (15169, "GOOGLE")
    ]
    assert isinstance(json_host["avg_rtt"], float)
    assert isinstance(json_host["loss"], float)
    assert json_host["name"] == "dns.google"

    # Just verify that the dict is serializable as JSON.
    t.to_json()


def test_enricher_expired_cache():
    """
    Create a traceroute, then manipulate the enrichers
    ip_info_db PyRadix object to mark an entry as
    expired, to verify that the code works properly and
    the information for that prefix are retrieved again
    from the external sources.
    """

    raw = open("tests/data/traceroute/mtr_json_1.json").read()
    create_traceroute(raw)

    # After the first enrichment is performed, the function
    # that pulls IP information from external sources is
    # expected to be called 5 times.
    assert len(get_ip_info_from_external_sources_mock.call_args_list) == 5

    # Mark an enricher's cache entry as updated one year
    # ago, so it will be discarded during the next
    # enrichement process.
    enricher.ip_info_db.search_exact(
        "89.97.0.0/16"
    ).data["last_updated"] = datetime.datetime.utcnow() - datetime.timedelta(days=365)

    # Trigger a new enrichment for the same traceroute.
    create_traceroute(raw)

    # After marking one prefix as expired, the function
    # that fetches IP info from external sources is
    # expected to be called one more time, making the
    # total count equal 6.
    assert len(get_ip_info_from_external_sources_mock.call_args_list) == 6


def test_enricher_load_from_db(mocker):
    """
    Create a traceroute, then destroy the enricher and
    create a new one. At this point, the IP Info entries
    that were previously stored into the DB are loaded,
    and when a new enrichment is performed, we shouldn't
    see any queries performed towards the external
    sources.
    """

    raw = open("tests/data/traceroute/mtr_json_1.json").read()
    create_traceroute(raw)

    # After the first enrichment is performed, the function
    # that pulls IP information from external sources is
    # expected to be called 5 times.
    assert len(get_ip_info_from_external_sources_mock.call_args_list) == 5

    # Now destroy the enricher and create it from scratch.
    # IP Info entries that were previously retrieved will
    # be loaded from the DB.
    _setup_enricher(mocker)

    assert len(enricher.ip_info_db.prefixes()) == 5

    # Run a second enrichment process for the same traceroute.
    raw = open("tests/data/traceroute/mtr_json_1.json").read()
    create_traceroute(raw)

    # The number of calls to fetch info from external sources
    # should now be 0. The enricher (and the MagicMock) were
    # destroyed few steps above, thus the calls count reset
    # to zero.
    assert len(get_ip_info_from_external_sources_mock.call_args_list) == 0


def test_traceroute_to_text():

    def _normalize_text(s):
        # Normalizing the lines obtained from the Traceroute
        # object and those expected by the test case.
        # The expected text contains some blank lines, just
        # added here to make the string looking a bit better
        # inside this file. Also, since the editor removes
        # any trailing blank space from that string, to make
        # the expected text matching the real one I'm removing
        # trailing spaces from everywhere.
        return "\n".join([
            line.rstrip()
            for line in s.split("\n")
            if line.strip()
        ])

    raw = open("tests/data/traceroute/mtr_json_1.json").read()
    t = create_traceroute(raw)
    txt = t.to_text()
    print(txt)

    assert _normalize_text(txt) == _normalize_text("""
 Hop IP               Loss         RTT   Origin                               Reverse
  1. 192.168.1.254      0%     5.48 ms
  2. 10.1.131.181       0%    16.35 ms
  3. 10.250.139.186     0%    11.60 ms
  4. 10.254.0.217       0%    12.56 ms
  5. 89.97.200.190      0%    11.43 ms   AS12874  FASTWEB - Fastweb SpA
  6. 62.101.124.17      0%    59.78 ms   AS12874  FASTWEB - Fastweb SpA       62-101-124-17.fastres.net
  7. 209.85.168.64      0%    19.72 ms   AS15169  GOOGLE
  8. 216.239.51.9       0%    21.97 ms   AS15169  GOOGLE
  9. 216.239.50.241     0%    19.91 ms   AS15169  GOOGLE
 10. 8.8.8.8            0%    22.86 ms   AS15169  GOOGLE                      dns.google
""")

    # A traceroute having some hops represented by multiple
    # hosts.
    raw = open("tests/data/traceroute/bsd_1.txt").read()
    t = create_traceroute(raw)
    txt = t.to_text()
    print(txt)

    assert _normalize_text(txt) == _normalize_text("""
 Hop IP                     RTT   Origin                               Reverse
  1. 192.168.1.254      3.44 ms
  2. 10.1.131.181       9.76 ms
  3. 10.250.139.186    14.33 ms
  4. 10.254.0.217      12.85 ms
     10.254.0.221      13.18 ms
  5. 89.97.200.190     13.02 ms   AS12874  FASTWEB - Fastweb SpA
     89.97.200.201     12.93 ms   AS12874  FASTWEB - Fastweb SpA
     89.97.200.186     11.10 ms   AS12874  FASTWEB - Fastweb SpA
  6. 93.57.68.145      12.91 ms   AS12874  FASTWEB - Fastweb SpA
     93.57.68.149      15.66 ms   AS12874  FASTWEB - Fastweb SpA
  7. 193.201.28.33     27.09 ms                                        cloudflare-nap.namex.it
  8. 172.68.197.130    32.96 ms   AS13335  CLOUDFLARENET
     172.68.197.8      33.98 ms   AS13335  CLOUDFLARENET
  9. *
 10. *
""")

    # Just adding an entry to the enricher's local cache
    # so that we'll be able to see how a hop that traverses
    # an IX LAN looks like.
    enricher.add_ip_info_to_local_cache(
        IPDBInfo(
            prefix=IPv4Network("217.29.66.0/23"),
            origins=None,
            ixp_network=IXPNetwork(
                lan_name="Test LAN",
                ix_name="MIX-IT",
                ix_description="Milan Internet Exchange"
            )
        ),
        dispatch_to_others=False
    )
    raw = open("tests/data/traceroute/mtr_json_2.json").read()
    t = create_traceroute(raw)
    txt = t.to_text()
    print(txt)

    assert _normalize_text(txt) == _normalize_text("""
 Hop IP               Loss         RTT   Origin                               Reverse
  1. 192.168.1.254      0%     3.79 ms
  2. 10.1.131.181       0%    14.78 ms
  3. 10.250.139.190     0%    10.71 ms
  4. 10.254.0.221       0%    10.69 ms
  5. 89.97.200.201      0%    10.68 ms   AS12874  FASTWEB - Fastweb SpA
  6. 93.63.100.141      0%    19.02 ms   AS12874  FASTWEB - Fastweb SpA       93-63-100-141.ip27.fastwebnet.it
  7. 217.29.66.1        0%    22.22 ms   IX: MIX-IT                           mix-1.mix-it.net
  8. 217.29.76.16       0%    18.74 ms   AS16004  MIXITA-AS - MIX S.r.L....   kroot-server1.mix-it.net
""")

    # Changing the enricher's cache entry to fake a MOAS
    # (Multiple-Origin AS) prefix for the 5th hop.
    enricher.add_ip_info_to_local_cache(
        IPDBInfo(
            prefix=IPv4Network("94.198.103.142"),
            origins=[
                (65501, "Origin AS1 of a MOAS prefix"),
                (65502, "Origin AS2 of a MOAS prefix")
            ],
            ixp_network=None
        ),
        dispatch_to_others=False
    )
    raw = open("tests/data/traceroute/linux_2.txt").read()
    t = create_traceroute(raw)
    txt = t.to_text()
    print(txt)

    assert _normalize_text(txt) == _normalize_text("""
 Hop IP                     RTT   Origin                               Reverse
  1. 72.14.232.198     19.60 ms   AS15169  GOOGLE
  2. 94.198.103.149    19.54 ms   AS49367  ASSEFLOW - Seflow...        google-demarc.seflow.it
  3. *
  4. *
  5. 94.198.103.142    19.44 ms   AS65501  Origin AS1 of a MOAS...     mix.gw.mix-ddos.seflow.it
                                  AS65502  Origin AS2 of a MOAS...
  6. 217.29.72.146     13.63 ms   AS16004  MIXITA-AS - MIX S.r.L....   fw.mix-it.net
  7. *
  8. *
""")
