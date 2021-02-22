from rich_traceroute.traceroute.parsers.base import HopHost
from rich_traceroute.traceroute.parsers.win_tracert import WindowsTracertParser as tested_parser_class


def test_parser_win_tracert_1(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/win_tracert_1.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='10.1.0.1', loss=None, avg_rtt=0.0, min_rtt=0, max_rtt=0)],
        2: [HopHost(host='98.245.140.1', loss=None, avg_rtt=27.667, min_rtt=19.0, max_rtt=35.0)],
        3: [HopHost(host='68.85.105.201', loss=None, avg_rtt=15.667, min_rtt=9.0, max_rtt=27.0)],
        4: [HopHost(host='209.85.241.37', loss=None, avg_rtt=77.333, min_rtt=75.0, max_rtt=81.0)],
        5: [HopHost(host='209.85.248.102', loss=None, avg_rtt=87.333, min_rtt=84.0, max_rtt=91.0)],
        6: [HopHost(host='209.85.225.104', loss=None, avg_rtt=88.0, min_rtt=76.0, max_rtt=112.0)],
    }


def test_parser_win_tracert_2(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/win_tracert_2.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='172.16.0.5', loss=None, avg_rtt=0.0, min_rtt=0, max_rtt=0)],
        2: [HopHost(host='192.168.0.50', loss=None, avg_rtt=0.0, min_rtt=0, max_rtt=0)],
        3: [HopHost(host='122.56.168.186', loss=None, avg_rtt=3.667, min_rtt=2.0, max_rtt=6.0)],
        4: [HopHost(host='122.56.99.240', loss=None, avg_rtt=2.667, min_rtt=2.0, max_rtt=3.0)],
        5: [HopHost(host='122.56.99.243', loss=None, avg_rtt=3.0, min_rtt=3.0, max_rtt=3.0)],
        6: [HopHost(host='122.56.116.6', loss=None, avg_rtt=3.0, min_rtt=2.0, max_rtt=4.0)],
        7: [HopHost(host='122.56.116.5', loss=None, avg_rtt=7.333, min_rtt=2.0, max_rtt=16.0)],
        8: [],
    }


def test_parser_win_tracert_3(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/win_tracert_3.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='172.16.0.5', loss=None, avg_rtt=0.0, min_rtt=0, max_rtt=0)],
        2: [HopHost(host='192.168.0.50', loss=None, avg_rtt=0.667, min_rtt=0, max_rtt=1.0)],
        3: [HopHost(host='122.56.168.186', loss=None, avg_rtt=3.333, min_rtt=2.0, max_rtt=5.0)],
        4: [HopHost(host='122.56.99.240', loss=None, avg_rtt=2.333, min_rtt=2.0, max_rtt=3.0)],
        5: [HopHost(host='122.56.99.243', loss=None, avg_rtt=3.667, min_rtt=3.0, max_rtt=5.0)],
        6: [],
        7: [HopHost(host='122.56.116.5', loss=None, avg_rtt=2.667, min_rtt=2.0, max_rtt=3.0)],
        8: [HopHost(host='122.56.119.53', loss=None, avg_rtt=3.0, min_rtt=2.0, max_rtt=4.0)],
        9: [HopHost(host='202.50.232.242', loss=None, avg_rtt=27.0, min_rtt=27.0, max_rtt=27.0)],
        10: [HopHost(host='202.50.232.246', loss=None, avg_rtt=26.333, min_rtt=25.0, max_rtt=27.0)],
        11: [HopHost(host='72.14.217.100', loss=None, avg_rtt=27.0, min_rtt=26.0, max_rtt=28.0)],
        12: [HopHost(host='108.170.247.33', loss=None, avg_rtt=27.0, min_rtt=27.0, max_rtt=27.0)],
        13: [HopHost(host='209.85.250.139', loss=None, avg_rtt=27.0, min_rtt=27.0, max_rtt=27.0)],
        14: [HopHost(host='216.58.200.99', loss=None, avg_rtt=27.0, min_rtt=27.0, max_rtt=27.0)],
    }


def test_parser_win_tracert_4(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/win_tracert_4.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='192.168.1.1', loss=None, avg_rtt=1.0, min_rtt=1.0, max_rtt=1.0)],
        2: [HopHost(host='10.11.12.2', loss=None, avg_rtt=16.0, min_rtt=16.0, max_rtt=16.0)],
        3: [HopHost(host='10.12.13.14', loss=None, avg_rtt=25.333, min_rtt=17.0, max_rtt=42.0)],
        4: [HopHost(host='10.12.13.15', loss=None, avg_rtt=19.333, min_rtt=16.0, max_rtt=24.0)],
        5: [HopHost(host='192.0.2.1', loss=None, avg_rtt=22.0, min_rtt=17.0, max_rtt=26.0)],
        6: [HopHost(host='192.0.2.2', loss=None, avg_rtt=17.333, min_rtt=17.0, max_rtt=18.0)],
        7: [HopHost(host='1.1.1.1', loss=None, avg_rtt=17.0, min_rtt=17.0, max_rtt=17.0)],
    }
