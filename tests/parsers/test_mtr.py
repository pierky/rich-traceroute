from rich_traceroute.traceroute.parsers.base import HopHost
from rich_traceroute.traceroute.parsers.mtr import MTRParser as tested_parser_class


def test_parser_mtr_1(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/mtr_1.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='192.168.1.254', loss=0.0, avg_rtt=6.4, min_rtt=3.8, max_rtt=9.1)],
        2: [HopHost(host='10.1.131.181', loss=0.0, avg_rtt=9.2, min_rtt=9.0, max_rtt=9.5)],
        3: [HopHost(host='10.250.139.186', loss=0.0, avg_rtt=9.2, min_rtt=9.0, max_rtt=9.4)],
        4: [HopHost(host='10.254.0.217', loss=0.0, avg_rtt=9.5, min_rtt=9.4, max_rtt=9.5)],
        5: [HopHost(host='89.97.200.190', loss=0.0, avg_rtt=10.0, min_rtt=9.6, max_rtt=10.3)],
        6: [HopHost(host='62-101-124-17.fastres.net', loss=0.0, avg_rtt=18.4, min_rtt=18.1, max_rtt=18.7)],
        7: [HopHost(host='209.85.168.64', loss=0.0, avg_rtt=17.3, min_rtt=17.0, max_rtt=17.6)],
        8: [HopHost(host='216.239.51.9', loss=0.0, avg_rtt=19.8, min_rtt=19.5, max_rtt=20.2)],
        9: [HopHost(host='216.239.50.241', loss=0.0, avg_rtt=16.8, min_rtt=16.8, max_rtt=16.8)],
        10: [HopHost(host='dns.google', loss=0.0, avg_rtt=20.5, min_rtt=20.4, max_rtt=20.6)],
    }


def test_parser_mtr_2(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/mtr_2.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='192.168.1.254', loss=0.0, avg_rtt=3.4, min_rtt=2.9, max_rtt=3.7)],
        2: [HopHost(host='10.1.131.181', loss=0.0, avg_rtt=12.9, min_rtt=8.9, max_rtt=27.7)],
        3: [HopHost(host='10.250.139.190', loss=0.0, avg_rtt=12.0, min_rtt=10.7, max_rtt=14.8)],
        4: [HopHost(host='10.254.0.217', loss=0.0, avg_rtt=12.5, min_rtt=10.7, max_rtt=15.9)],
        5: [HopHost(host='89.97.200.197', loss=0.0, avg_rtt=12.2, min_rtt=10.5, max_rtt=14.7)],
        6: [HopHost(host='93.57.68.145', loss=0.0, avg_rtt=13.1, min_rtt=11.6, max_rtt=14.6)],
        7: [HopHost(host='cloudflare-nap.namex.it', loss=0.0, avg_rtt=25.8, min_rtt=23.8, max_rtt=28.7)],
        8: [HopHost(host='172.68.197.126', loss=0.0, avg_rtt=30.5, min_rtt=24.8, max_rtt=33.8)],
        9: [HopHost(host='172.68.197.93', loss=0.0, avg_rtt=28.7, min_rtt=25.4, max_rtt=32.2)],
        10: [],
        11: [HopHost(host='text-lb.esams.wikimedia.org', loss=0.0, avg_rtt=49.6, min_rtt=48.3, max_rtt=50.8)],
    }
