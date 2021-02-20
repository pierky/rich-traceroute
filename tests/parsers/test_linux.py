from rich_traceroute.traceroute.parsers.base import HopHost
from rich_traceroute.traceroute.parsers.linux import LinuxParser as tested_parser_class


def test_parser_linux_1(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/linux_1.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='62.115.153.214', loss=None, avg_rtt=1.754, min_rtt=1.606, max_rtt=1.862)],
        2: [HopHost(host='62.115.116.17', loss=None, avg_rtt=1.736, min_rtt=1.701, max_rtt=1.767)],
        3: [HopHost(host='213.248.100.197', loss=None, avg_rtt=1.803, min_rtt=1.626, max_rtt=1.894)],
        4: [HopHost(host='185.235.236.46', loss=None, avg_rtt=1.339, min_rtt=1.314, max_rtt=1.36)],
        5: [HopHost(host='185.235.236.4', loss=None, avg_rtt=1.424, min_rtt=1.228, max_rtt=1.62),
            HopHost(host='185.235.236.8', loss=None, avg_rtt=1.606, min_rtt=1.606, max_rtt=1.606)],
        6: [HopHost(host='185.235.236.197', loss=None, avg_rtt=1.322, min_rtt=1.244, max_rtt=1.44)],
    }


def test_parser_linux_2(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/linux_2.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='72.14.232.198', loss=None, avg_rtt=19.603, min_rtt=19.596, max_rtt=19.608)],
        2: [HopHost(host='94.198.103.149', loss=None, avg_rtt=19.542, min_rtt=19.535, max_rtt=19.555)],
        3: [],
        4: [],
        5: [HopHost(host='94.198.103.142', loss=None, avg_rtt=19.443, min_rtt=19.428, max_rtt=19.454)],
        6: [HopHost(host='217.29.72.146', loss=None, avg_rtt=13.627, min_rtt=10.738, max_rtt=19.344)],
        7: [],
        8: [],
    }


def test_parser_linux_3(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/linux_3.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='2001:db8:0:f101::1', loss=None, avg_rtt=1.109, min_rtt=0.407, max_rtt=1.566)],
        2: [HopHost(host='3ffe:2000:0:400::1', loss=None, avg_rtt=91.588, min_rtt=90.431, max_rtt=92.377)],
        3: [HopHost(host='3ffe:2000:0:1::132', loss=None, avg_rtt=113.828, min_rtt=107.982, max_rtt=118.945)],
        4: [HopHost(host='3ffe:c00:8023:2b::2', loss=None, avg_rtt=978.434, min_rtt=968.468, max_rtt=993.392)],
        5: [HopHost(host='3ffe:2e00:e:c::3', loss=None, avg_rtt=507.42, min_rtt=505.549, max_rtt=508.928)],
        6: [HopHost(host='3ffe:b00:c18:1::10', loss=None, avg_rtt=1285.295, min_rtt=1265.85, max_rtt=1304.74)],
    }


def test_parser_linux_4(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/linux_4.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='2001:a61:2001:db8::', loss=None, avg_rtt=0.525, min_rtt=0.41, max_rtt=0.655)],
        2: [HopHost(host='2001:a60::89:705:1', loss=None, avg_rtt=34.189, min_rtt=26.428, max_rtt=41.777)],
        3: [HopHost(host='2001:a60::89:0:1:2', loss=None, avg_rtt=19.181, min_rtt=19.131, max_rtt=19.248)],
        4: [HopHost(host='2001:a60:0:106::2', loss=None, avg_rtt=20.463, min_rtt=20.457, max_rtt=20.467)],
        5: [HopHost(host='2001:4860::9:4000:cf86', loss=None, avg_rtt=21.844, min_rtt=21.836, max_rtt=21.852)],
        6: [HopHost(host='2001:4860:0:1::19', loss=None, avg_rtt=22.065, min_rtt=21.585, max_rtt=22.919)],
        7: [HopHost(host='2a00:1450:4016:804::200e', loss=None, avg_rtt=20.85, min_rtt=19.31, max_rtt=23.176)],
    }


def test_parser_linux_5(parser_ctx):
    p = parser_ctx.parse_test_file(
        "tests/data/traceroute/linux_5.txt",
        tested_parser_class
    )
    assert p.hops == {
        1: [HopHost(host='local_host_name', loss=None, avg_rtt=1.196, min_rtt=0.885, max_rtt=1.423)],
        2: [HopHost(host='2001:db8:100::1:1a', loss=None, avg_rtt=0.287, min_rtt=0.237, max_rtt=0.386)],
        3: [HopHost(host='another_local_host_name', loss=None, avg_rtt=67.957, min_rtt=39.849, max_rtt=116.046)],
        4: [HopHost(host='2001:db8:1:2:2:4680:0:1', loss=None, avg_rtt=21.443, min_rtt=21.443, max_rtt=21.443),
            HopHost(host='2001:db8:1:2:2:42e5:0:1', loss=None, avg_rtt=21.297, min_rtt=21.287, max_rtt=21.306)],
        5: [],
    }
