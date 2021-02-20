import ipaddress

from rich_traceroute.enrichers.enricher import Enricher


def test_mock_get_hostname_from_ip():
    assert Enricher._get_hostname_from_ip(
        ipaddress.ip_address("8.8.8.8")
    ) == "dns.google"
