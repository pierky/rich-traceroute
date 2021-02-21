from rich_traceroute.traceroute.parsers.base import HopHost
from rich_traceroute.traceroute.parsers.winmtr import WinMTRParser as tested_parser_class


def test_parser_winmtr_1(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/winmtr_1.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='192.168.1.1', loss=0.0, avg_rtt=0.0, min_rtt=0.0, max_rtt=3.0)],
        2: [],
        3: [HopHost(host='172.17.217.48', loss=0.0, avg_rtt=9.0, min_rtt=7.0, max_rtt=20.0)],
        4: [HopHost(host='172.17.218.156', loss=0.0, avg_rtt=11.0, min_rtt=8.0, max_rtt=26.0)],
        5: [HopHost(host='172.19.184.14', loss=0.0, avg_rtt=10.0, min_rtt=9.0, max_rtt=21.0)],
        6: [HopHost(host='172.19.177.26', loss=0.0, avg_rtt=13.0, min_rtt=10.0, max_rtt=27.0)],
        7: [HopHost(host='192.168.205.98', loss=0.0, avg_rtt=14.0, min_rtt=10.0, max_rtt=29.0)],
        8: [HopHost(host='10.1.109.236', loss=0.0, avg_rtt=13.0, min_rtt=11.0, max_rtt=29.0)],
        9: [HopHost(host='10.1.138.234', loss=0.0, avg_rtt=14.0, min_rtt=12.0, max_rtt=29.0)],
        10: [HopHost(host='10.2.69.253', loss=0.0, avg_rtt=15.0, min_rtt=13.0, max_rtt=29.0)],
        11: [HopHost(host='8.8.8.8', loss=0.0, avg_rtt=13.0, min_rtt=10.0, max_rtt=29.0)],
    }
