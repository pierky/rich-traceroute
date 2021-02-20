import pytest
from unittest.mock import MagicMock, call
import ipaddress


from rich_traceroute.enrichers.ixp_networks import IXPNetworksUpdater
from rich_traceroute.structures import IPDBInfo, IXPNetwork


# Will be set by the fixture and made available to the
# test case function for inspection.
updater_dispatch_ip_info_mock = None


@pytest.fixture(autouse=True)
def mock_updater(mocker):

    global updater_dispatch_ip_info_mock
    updater_dispatch_ip_info_mock = MagicMock(
        "rich_traceroute.enrichers.ixp_networks.IXPNetworksUpdater._dispatch_ip_info"
    )

    mocker.patch(
        "rich_traceroute.enrichers.ixp_networks.IXPNetworksUpdater._dispatch_ip_info",
        updater_dispatch_ip_info_mock
    )


def test_ixp_networks_1(db):
    updater = IXPNetworksUpdater()

    updater._build_ixp_networks()

    expected_call = call(
        IPDBInfo(
            prefix=ipaddress.ip_network("217.29.66.0/23"),
            origins=None,
            ixp_network=IXPNetwork(
                lan_name=None,
                ix_name="MIX-IT",
                ix_description="Milan Internet eXchange"
            )
        )
    )
    assert expected_call in updater_dispatch_ip_info_mock.call_args_list
