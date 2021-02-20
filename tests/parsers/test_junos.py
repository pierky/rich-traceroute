from rich_traceroute.traceroute.parsers.base import HopHost
from rich_traceroute.traceroute.parsers.junos import JunosParser as tested_parser_class


def test_parser_junos_1(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/junos_1.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='10.1.2.185', loss=0.0, avg_rtt=1.7, min_rtt=0.6, max_rtt=8.3)],
        2: [HopHost(host='10.2.2.234', loss=0.0, avg_rtt=239.2, min_rtt=239.1, max_rtt=239.3)],
        3: [HopHost(host='10.2.3.190', loss=10.0, avg_rtt=2.4, min_rtt=1.7, max_rtt=2.9)],
        4: [HopHost(host='10.2.2.111', loss=20.0, avg_rtt=76.4, min_rtt=75.1, max_rtt=82.1)],
        5: [HopHost(host='10.2.3.189', loss=50.0, avg_rtt=132.7, min_rtt=131.4, max_rtt=134.2)],
        6: [HopHost(host='10.2.3.192', loss=80.0, avg_rtt=243.5, min_rtt=242.0, max_rtt=245.1)],
        7: [HopHost(host='10.2.6.133', loss=0.0, avg_rtt=246.3, min_rtt=246.0, max_rtt=246.9)],
        8: [HopHost(host='10.2.2.246', loss=0.0, avg_rtt=240.5, min_rtt=240.0, max_rtt=241.4)],
        9: [HopHost(host='10.3.177.106', loss=0.0, avg_rtt=236.9, min_rtt=236.6, max_rtt=238.4)],
        10: [],
        11: [],
        12: [HopHost(host='10.4.81.34', loss=0.0, avg_rtt=245.6, min_rtt=244.7, max_rtt=249.8)],
        13: [],
        14: [],
        15: [HopHost(host='10.5.5.143', loss=11.1, avg_rtt=243.3, min_rtt=243.1, max_rtt=243.8)],
    }
