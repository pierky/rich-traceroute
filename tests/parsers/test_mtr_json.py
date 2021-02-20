from rich_traceroute.traceroute.parsers.base import HopHost
from rich_traceroute.traceroute.parsers.mtr_json import MTRJSONParser as tested_parser_class


def test_parser_mtr_json_1(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/mtr_json_1.json",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='192.168.1.254', loss=0.0, avg_rtt=5.48, min_rtt=3.65, max_rtt=10.55)],
        2: [HopHost(host='10.1.131.181', loss=0.0, avg_rtt=16.35, min_rtt=10.26, max_rtt=37.55)],
        3: [HopHost(host='10.250.139.186', loss=0.0, avg_rtt=11.6, min_rtt=11.2, max_rtt=11.98)],
        4: [HopHost(host='10.254.0.217', loss=0.0, avg_rtt=12.56, min_rtt=11.03, max_rtt=17.78)],
        5: [HopHost(host='89.97.200.190', loss=0.0, avg_rtt=11.43, min_rtt=10.98, max_rtt=12.35)],
        6: [HopHost(host='62-101-124-17.fastres.net', loss=0.0, avg_rtt=59.78, min_rtt=20.25, max_rtt=101.01)],
        7: [HopHost(host='209.85.168.64', loss=0.0, avg_rtt=19.72, min_rtt=19.52, max_rtt=19.92)],
        8: [HopHost(host='216.239.51.9', loss=0.0, avg_rtt=21.97, min_rtt=21.43, max_rtt=22.67)],
        9: [HopHost(host='216.239.50.241', loss=0.0, avg_rtt=19.91, min_rtt=19.45, max_rtt=20.51)],
        10: [HopHost(host='dns.google', loss=0.0, avg_rtt=22.86, min_rtt=22.01, max_rtt=23.3)],
    }


def test_parser_mtr_json_2(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/mtr_json_2.json",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='192.168.1.254', loss=0.0, avg_rtt=3.79, min_rtt=3.33, max_rtt=4.06)],
        2: [HopHost(host='10.1.131.181', loss=0.0, avg_rtt=14.78, min_rtt=9.21, max_rtt=34.42)],
        3: [HopHost(host='10.250.139.190', loss=0.0, avg_rtt=10.71, min_rtt=10.08, max_rtt=11.5)],
        4: [HopHost(host='10.254.0.221', loss=0.0, avg_rtt=10.69, min_rtt=9.12, max_rtt=11.7)],
        5: [HopHost(host='89.97.200.201', loss=0.0, avg_rtt=10.68, min_rtt=10.03, max_rtt=11.07)],
        6: [HopHost(host='93.63.100.141', loss=0.0, avg_rtt=19.02, min_rtt=18.47, max_rtt=20.02)],
        7: [HopHost(host='217.29.66.1', loss=0.0, avg_rtt=22.22, min_rtt=21.72, max_rtt=22.51)],
        8: [HopHost(host='217.29.76.16', loss=0.0, avg_rtt=18.74, min_rtt=18.38, max_rtt=19.07)],
    }


def test_parser_mtr_json_3(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/mtr_json_3.json",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='192.168.2.254', loss=0.0, avg_rtt=0.5, min_rtt=0.5, max_rtt=0.5)],
        2: [HopHost(host='10.0.0.1', loss=0.0, avg_rtt=2.7, min_rtt=1.9, max_rtt=3.7)],
        3: [HopHost(host='10.1.0.1', loss=0.0, avg_rtt=3.6, min_rtt=1.3, max_rtt=6.3)],
        4: [HopHost(host='10.2.0.1', loss=0.0, avg_rtt=3.0, min_rtt=2.2, max_rtt=3.9)],
        5: [HopHost(host='10.3.0.1', loss=0.0, avg_rtt=1.9, min_rtt=1.2, max_rtt=3.0)],
        6: [HopHost(host='10.4.0.1', loss=0.0, avg_rtt=3.3, min_rtt=2.0, max_rtt=4.0)],
        7: [HopHost(host='10.5.0.1', loss=0.0, avg_rtt=3.1, min_rtt=2.4, max_rtt=4.1)],
        8: [HopHost(host='10.6.0.1', loss=0.0, avg_rtt=5.9, min_rtt=5.0, max_rtt=6.8)],
        9: [HopHost(host='10.7.0.1', loss=0.0, avg_rtt=12.9, min_rtt=6.7, max_rtt=32.8)],
        10: [HopHost(host='10.8.0.1', loss=0.0, avg_rtt=7.5, min_rtt=6.4, max_rtt=8.2)],
        11: [HopHost(host='10.9.0.1', loss=0.0, avg_rtt=5.4, min_rtt=4.5, max_rtt=6.4)],
        12: [HopHost(host='8.8.8.8', loss=0.0, avg_rtt=5.6, min_rtt=4.4, max_rtt=6.5)],
    }
