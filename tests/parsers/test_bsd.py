from rich_traceroute.traceroute.parsers.base import HopHost
from rich_traceroute.traceroute.parsers.bsd import BSDParser as tested_parser_class


def test_parser_bsd_1(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/bsd_1.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost('192.168.1.254', None, 3.444, 3.118, 3.641)],
        2: [HopHost('10.1.131.181', None, 9.759, 9.465, 10.311)],
        3: [HopHost('10.250.139.186', None, 14.33, 14.007, 14.967)],
        4: [HopHost('10.254.0.217', None, 12.849, 12.522, 13.175),
            HopHost('10.254.0.221', None, 13.178, 13.178, 13.178)],
        5: [HopHost('89.97.200.190', None, 13.019, 13.019, 13.019),
            HopHost('89.97.200.201', None, 12.929, 12.929, 12.929),
            HopHost('89.97.200.186', None, 11.096, 11.096, 11.096)],
        6: [HopHost('93.57.68.145', None, 12.909, 11.639, 14.18),
            HopHost('93.57.68.149', None, 15.658, 15.658, 15.658)],
        7: [HopHost('193.201.28.33', None, 27.094, 26.245, 28.388)],
        8: [HopHost('172.68.197.130', None, 32.96, 32.96, 32.96),
            HopHost('172.68.197.8', None, 33.978, 33.756, 34.2)],
        9: [],
        10: [],
    }


def test_parser_bsd_2(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/bsd_2.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='128.3.112.1', loss=None, avg_rtt=12.667, min_rtt=0.0, max_rtt=19.0)],
        2: [HopHost(host='128.32.216.1', loss=None, avg_rtt=32.333, min_rtt=19.0, max_rtt=39.0)],
        3: [HopHost(host='128.32.216.1', loss=None, avg_rtt=32.333, min_rtt=19.0, max_rtt=39.0)],
        4: [HopHost(host='128.32.136.23', loss=None, avg_rtt=39.333, min_rtt=39.0, max_rtt=40.0)],
        5: [HopHost(host='128.32.168.22', loss=None, avg_rtt=39.0, min_rtt=39.0, max_rtt=39.0)],
        6: [HopHost(host='128.32.197.4', loss=None, avg_rtt=52.667, min_rtt=40.0, max_rtt=59.0)],
        7: [HopHost(host='131.119.2.5', loss=None, avg_rtt=59.0, min_rtt=59.0, max_rtt=59.0)],
        8: [HopHost(host='129.140.70.13', loss=None, avg_rtt=92.667, min_rtt=80.0, max_rtt=99.0)],
        9: [HopHost(host='129.140.71.6', loss=None, avg_rtt=232.333, min_rtt=139.0, max_rtt=319.0)],
        10: [HopHost(host='129.140.81.7', loss=None, avg_rtt=206.0, min_rtt=199.0, max_rtt=220.0)],
        11: [HopHost(host='35.1.1.48', loss=None, avg_rtt=239.0, min_rtt=239.0, max_rtt=239.0)],
    }


def test_parser_bsd_3(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/bsd_3.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='128.3.112.1', loss=None, avg_rtt=0.0, min_rtt=0.0, max_rtt=0.0)],
        2: [HopHost(host='128.32.216.1', loss=None, avg_rtt=19.0, min_rtt=19.0, max_rtt=19.0)],
        3: [HopHost(host='128.32.216.1', loss=None, avg_rtt=25.667, min_rtt=19.0, max_rtt=39.0)],
        4: [HopHost(host='128.32.136.23', loss=None, avg_rtt=32.333, min_rtt=19.0, max_rtt=39.0)],
        5: [HopHost(host='128.32.168.22', loss=None, avg_rtt=32.667, min_rtt=20.0, max_rtt=39.0)],
        6: [HopHost(host='128.32.197.4', loss=None, avg_rtt=72.333, min_rtt=39.0, max_rtt=119.0)],
        7: [HopHost(host='131.119.2.5', loss=None, avg_rtt=52.333, min_rtt=39.0, max_rtt=59.0)],
        8: [HopHost(host='129.140.70.13', loss=None, avg_rtt=86.0, min_rtt=79.0, max_rtt=99.0)],
        9: [HopHost(host='129.140.71.6', loss=None, avg_rtt=145.667, min_rtt=139.0, max_rtt=159.0)],
        10: [HopHost(host='129.140.81.7', loss=None, avg_rtt=226.333, min_rtt=180.0, max_rtt=300.0)],
        11: [HopHost(host='129.140.72.17', loss=None, avg_rtt=259.333, min_rtt=239.0, max_rtt=300.0)],
        12: [],
        13: [HopHost(host='128.121.54.72', loss=None, avg_rtt=345.667, min_rtt=259.0, max_rtt=499.0)],
        14: [],
        15: [],
        16: [],
        17: [],
        18: [HopHost(host='18.26.0.115', loss=None, avg_rtt=299.0, min_rtt=279.0, max_rtt=339.0)],
    }


def test_parser_bsd_4(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/bsd_4.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='128.3.112.1', loss=None, avg_rtt=0.0, min_rtt=0.0, max_rtt=0.0)],
        2: [HopHost(host='128.32.216.1', loss=None, avg_rtt=32.333, min_rtt=19.0, max_rtt=39.0)],
        3: [HopHost(host='128.32.216.1', loss=None, avg_rtt=25.667, min_rtt=19.0, max_rtt=39.0)],
        4: [HopHost(host='128.32.136.23', loss=None, avg_rtt=32.667, min_rtt=19.0, max_rtt=40.0)],
        5: [HopHost(host='128.32.168.35', loss=None, avg_rtt=39.0, min_rtt=39.0, max_rtt=39.0)],
        6: [HopHost(host='128.32.133.254', loss=None, avg_rtt=45.667, min_rtt=39.0, max_rtt=59.0)],
        7: [],
        8: [],
        9: [],
        10: [],
        11: [],
        12: [],
        13: [HopHost(host='128.32.131.22', loss=None, avg_rtt=45.667, min_rtt=39.0, max_rtt=59.0)],
    }
