from rich_traceroute.enrichers.dns import ip_to_name, name_to_ip


def test_dns_name_to_ip():
    assert name_to_ip("one.one.one.one") in ("1.1.1.1", "1.0.0.1")


def test_dns_ip_to_name():
    assert ip_to_name("1.1.1.1") == "one.one.one.one"
