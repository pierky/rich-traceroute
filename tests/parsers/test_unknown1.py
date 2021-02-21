from rich_traceroute.traceroute.parsers.base import HopHost
from rich_traceroute.traceroute.parsers.unknown1 import UnknownFormat1Parser as tested_parser_class


def test_parser_unknown1_1(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/unknown1_1.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='_gateway', loss=None, avg_rtt=0.889, min_rtt=0.874, max_rtt=0.905)],
        2: [HopHost(host='hostname1', loss=None, avg_rtt=10.599, min_rtt=10.599, max_rtt=10.599)],
        3: [HopHost(host='192.0.2.1', loss=None, avg_rtt=11.419, min_rtt=11.419, max_rtt=11.419)],
        4: [HopHost(host='192.0.2.2', loss=None, avg_rtt=10.929, min_rtt=10.929, max_rtt=10.929)],
        5: [HopHost(host='peer8-et-3-0-2.example.com', loss=None, avg_rtt=11.096, min_rtt=11.096, max_rtt=11.096)],
        6: [HopHost(host='10.0.0.1', loss=None, avg_rtt=10.909, min_rtt=10.909, max_rtt=10.909)],
        7: [HopHost(host='ae24.net.example.com', loss=None, avg_rtt=11.195, min_rtt=11.195, max_rtt=11.195)],
        8: [HopHost(host='ae28.net.example.com', loss=None, avg_rtt=11.332, min_rtt=11.332, max_rtt=11.332)],
        9: [HopHost(host='ae31.net.example.com', loss=None, avg_rtt=15.583, min_rtt=15.583, max_rtt=15.583)],
        10: [HopHost(host='ae29.net.example.com', loss=None, avg_rtt=20.834, min_rtt=20.834, max_rtt=20.834)],
    }
