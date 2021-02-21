from rich_traceroute.traceroute.parsers.base import HopHost
from rich_traceroute.traceroute.parsers.mtr import MTRParserInteractive as tested_parser_class


def test_parser_mtr_interactive_1(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/mtr_interactive_1.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='192.168.1.254', loss=0.0, avg_rtt=11.6, min_rtt=2.0, max_rtt=50.7)],
        2: [HopHost(host='10.1.131.181', loss=0.0, avg_rtt=38.3, min_rtt=8.8, max_rtt=112.8)],
        3: [HopHost(host='10.250.139.186', loss=0.0, avg_rtt=41.6, min_rtt=9.9, max_rtt=142.4)],
        4: [HopHost(host='10.254.0.217', loss=0.0, avg_rtt=22.1, min_rtt=10.0, max_rtt=57.9)],
        5: [HopHost(host='89.97.200.190', loss=0.0, avg_rtt=29.0, min_rtt=9.4, max_rtt=123.4)],
        6: [HopHost(host='62-101-124-17.fastres.net', loss=0.0, avg_rtt=27.4, min_rtt=18.5, max_rtt=93.6)],
        7: [HopHost(host='209.85.168.64', loss=0.0, avg_rtt=41.0, min_rtt=21.6, max_rtt=108.8)],
        8: [HopHost(host='216.239.51.9', loss=0.0, avg_rtt=32.1, min_rtt=19.9, max_rtt=147.4)],
        9: [HopHost(host='216.239.50.241', loss=0.0, avg_rtt=34.0, min_rtt=21.4, max_rtt=76.2)],
        10: [HopHost(host='dns.google', loss=0.0, avg_rtt=66.5, min_rtt=21.3, max_rtt=172.5)],
    }


def test_parser_mtr_interactive_2(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/mtr_interactive_2.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='192.168.1.254', loss=20.0, avg_rtt=2.6, min_rtt=2.3, max_rtt=3.2)],
        2: [HopHost(host='10.1.131.181', loss=0.0, avg_rtt=9.9, min_rtt=9.1, max_rtt=11.2)],
        3: [HopHost(host='10.250.139.186', loss=0.0, avg_rtt=10.0, min_rtt=9.5, max_rtt=10.6)],
        4: [HopHost(host='10.254.0.217', loss=0.0, avg_rtt=10.2, min_rtt=9.0, max_rtt=11.0)],
        5: [HopHost(host='89.97.200.190', loss=0.0, avg_rtt=10.3, min_rtt=9.5, max_rtt=11.9)],
        6: [HopHost(host='62-101-124-17.fastres.net', loss=0.0, avg_rtt=19.3, min_rtt=18.9, max_rtt=20.1)],
        7: [HopHost(host='209.85.168.64', loss=0.0, avg_rtt=21.2, min_rtt=20.8, max_rtt=21.7)],
        8: [HopHost(host='216.239.51.9', loss=0.0, avg_rtt=20.1, min_rtt=19.6, max_rtt=20.6)],
        9: [HopHost(host='216.239.50.241', loss=0.0, avg_rtt=21.7, min_rtt=21.0, max_rtt=22.1)],
        10: [HopHost(host='dns.google', loss=0.0, avg_rtt=21.4, min_rtt=20.9, max_rtt=22.2)],
    }


def test_parser_mtr_interactive_3(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/mtr_interactive_3.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='192.168.1.254', loss=0.0, avg_rtt=4.1, min_rtt=2.5, max_rtt=8.9)],
        2: [HopHost(host='10.1.131.181', loss=0.0, avg_rtt=14.9, min_rtt=8.3, max_rtt=38.9)],
        3: [HopHost(host='10.250.139.186', loss=0.0, avg_rtt=10.0, min_rtt=9.4, max_rtt=10.8)],
        4: [HopHost(host='10.254.0.217', loss=0.0, avg_rtt=10.0, min_rtt=9.6, max_rtt=10.3)],
        5: [],
    }
