from rich_traceroute.traceroute.parsers.base import HopHost
from rich_traceroute.traceroute.parsers.iosxr import IOSXRParser as tested_parser_class


def test_parser_iosxr_1(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/iosxr_1.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='1.2.3.4', loss=None, avg_rtt=0.333, min_rtt=0.0, max_rtt=1.0)],
        2: [HopHost(host='1.2.5.6', loss=None, avg_rtt=89.667, min_rtt=88.0, max_rtt=91.0)],
        3: [HopHost(host='1.2.7.8', loss=None, avg_rtt=89.5, min_rtt=89.0, max_rtt=90.0)],
        4: [HopHost(host='3.4.5.6', loss=None, avg_rtt=117.0, min_rtt=117.0, max_rtt=117.0)],
        5: [HopHost(host='1.2.1.2', loss=None, avg_rtt=125.0, min_rtt=125.0, max_rtt=125.0),
            HopHost(host='1.2.2.1', loss=None, avg_rtt=120.0, min_rtt=120.0, max_rtt=120.0)],
        6: [],
        7: [],
    }


def test_parser_iosxr_2(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/iosxr_2.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='192.168.0.1', loss=None, avg_rtt=0.667, min_rtt=0.0, max_rtt=1.0)],
        2: [HopHost(host='10.5.226.206', loss=None, avg_rtt=98.5, min_rtt=98.0, max_rtt=99.0),
            HopHost(host='10.7.110.97', loss=None, avg_rtt=98.0, min_rtt=98.0, max_rtt=98.0)],
        3: [HopHost(host='10.11.128.50', loss=None, avg_rtt=97.333, min_rtt=97.0, max_rtt=98.0)],
        4: [HopHost(host='10.12.66.97', loss=None, avg_rtt=241.0, min_rtt=241.0, max_rtt=241.0),
            HopHost(host='10.11.128.50', loss=None, avg_rtt=97.0, min_rtt=97.0, max_rtt=97.0)],
        5: [HopHost(host='10.12.3.38', loss=None, avg_rtt=237.0, min_rtt=236.0, max_rtt=239.0)],
        6: [HopHost(host='10.12.3.38', loss=None, avg_rtt=236.5, min_rtt=236.0, max_rtt=237.0),
            HopHost(host='10.12.4.194', loss=None, avg_rtt=240.0, min_rtt=240.0, max_rtt=240.0)],
        7: [HopHost(host='10.12.2.166', loss=None, avg_rtt=241.333, min_rtt=240.0, max_rtt=242.0)],
        8: [HopHost(host='10.12.3.145', loss=None, avg_rtt=240.0, min_rtt=240.0, max_rtt=240.0),
            HopHost(host='10.12.2.166', loss=None, avg_rtt=241.0, min_rtt=241.0, max_rtt=241.0)],
        9: [HopHost(host='10.13.36.121', loss=None, avg_rtt=262.333, min_rtt=262.0, max_rtt=263.0)],
    }
