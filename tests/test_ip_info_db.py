import ipaddress
import datetime
import time

from rich_traceroute.ip_info_db import (
    IPInfo_Prefix,
    IPInfo_Origin,
    IPInfo_IXPNetwork,
    remove_old_entries
)
from rich_traceroute.structures import IPDBInfo, IXPNetwork


def test_ip_info_db_1(db):
    """Basic test, create an IPInfo record."""
    ipdb_info = IPDBInfo(
        prefix=ipaddress.ip_network("192.0.2.0/24"),
        origins=[
            (65534, "test")
        ],
        ixp_network=IXPNetwork(
            lan_name="test LAN",
            ix_name="test IX",
            ix_description="test description"
        )
    )

    IPInfo_Prefix.create_from_ipdbinfo(ipdb_info)

    prefixes = IPInfo_Prefix.select()
    assert len(prefixes) == 1

    prefix = prefixes[0]
    assert prefix.prefix == ipaddress.ip_network("192.0.2.0/24")
    assert prefix.origins == [(65534, "test")]
    assert prefix.ixp_network.lan_name == "test LAN"
    assert prefix.ixp_network.ix_name == "test IX"
    assert prefix.ixp_network.ix_description == "test description"

    origins = IPInfo_Origin.select()
    assert len(origins) == 1

    ipx_networks = IPInfo_IXPNetwork.select()
    assert len(ipx_networks) == 1

    assert prefix.to_ipdbinfo() == ipdb_info

    # To be sure that the DB/Python conversion works
    # properly and keeps the right data type.
    assert isinstance(
        prefix.to_ipdbinfo().prefix,
        (ipaddress.IPv4Network, ipaddress.IPv6Network)
    )
    assert isinstance(
        prefix.to_ipdbinfo().ixp_network, IXPNetwork
    )


def test_ip_info_db_2(db):
    """Create a record and then update it."""
    ipdb_info = IPDBInfo(
        prefix=ipaddress.ip_network("192.0.2.0/24"),
        origins=[
            (65534, "test")
        ],
        ixp_network=None
    )

    prefix_original = IPInfo_Prefix.create_from_ipdbinfo(ipdb_info)

    original_dt = prefix_original.last_updated

    time.sleep(0.5)

    prefix_updated = IPInfo_Prefix.create_from_ipdbinfo(ipdb_info)

    # Check that the last_updated reflects the actual
    # update date&time.
    updated_dt = prefix_updated.last_updated

    prefixes = IPInfo_Prefix.select()

    # We want to see only 1 prefix, to be sure the
    # original one was update and that a new one
    # was not created.
    assert len(prefixes) == 1

    prefix = prefixes[0]
    assert prefix.prefix == ipaddress.ip_network("192.0.2.0/24")
    assert prefix.origins == [(65534, "test")]

    origins = IPInfo_Origin.select()

    # Similarly to above, only one origin must be found.
    assert len(origins) == 1

    assert updated_dt >= original_dt + datetime.timedelta(milliseconds=500)


def test_ip_info_db_3(db):
    """Create two records and then update one of them."""
    ipdb_info_1 = IPDBInfo(
        prefix=ipaddress.ip_network("192.0.2.0/25"),
        origins=[
            (65501, "test 1 a"),
            (65502, "test 1 b")
        ],
        ixp_network=None
    )

    ipdb_info_2 = IPDBInfo(
        prefix=ipaddress.ip_network("192.0.2.128/25"),
        origins=[
            (65511, "test 2")
        ],
        ixp_network=None
    )

    IPInfo_Prefix.create_from_ipdbinfo(ipdb_info_1)
    IPInfo_Prefix.create_from_ipdbinfo(ipdb_info_2)

    # Perform the same checks twice; at the end of the
    # first iteration, the prefix 1 is updated.
    for i in [1, 2]:

        prefixes = IPInfo_Prefix.select()
        assert len(prefixes) == 2

        origins = IPInfo_Origin.select()
        assert len(origins) == 3

        prefix = [p for p in prefixes
                  if p.prefix == ipaddress.ip_network("192.0.2.0/25")][0]

        assert prefix.origins == [
            (65501, "test 1 a"),
            (65502, "test 1 b")
        ]

        prefix = [p for p in prefixes
                  if p.prefix == ipaddress.ip_network("192.0.2.128/25")][0]

        assert prefix.origins == [
            (65511, "test 2")
        ]

        if i == 1:
            IPInfo_Prefix.create_from_ipdbinfo(ipdb_info_1)


def test_ip_info_db_4(db):
    """A record with no origins and only IXP network"""
    ipdb_info = IPDBInfo(
        prefix=ipaddress.ip_network("192.0.2.0/24"),
        origins=None,
        ixp_network=IXPNetwork(
            lan_name="test LAN",
            ix_name="test IX",
            ix_description="test description"
        )
    )

    IPInfo_Prefix.create_from_ipdbinfo(ipdb_info)

    prefixes = IPInfo_Prefix.select()
    assert len(prefixes) == 1

    prefix = prefixes[0]
    assert prefix.prefix == ipaddress.ip_network("192.0.2.0/24")
    assert prefix.origins is None
    assert prefix.ixp_network.lan_name == "test LAN"
    assert prefix.ixp_network.ix_name == "test IX"
    assert prefix.ixp_network.ix_description == "test description"

    origins = IPInfo_Origin.select()
    assert len(origins) == 0

    ipx_networks = IPInfo_IXPNetwork.select()
    assert len(ipx_networks) == 1

    assert prefix.to_ipdbinfo() == ipdb_info


def test_ip_info_db_5(db):
    """A record with no IXP network and only origins"""
    ipdb_info = IPDBInfo(
        prefix=ipaddress.ip_network("192.0.2.0/24"),
        origins=[
            (65511, "test 2")
        ],
        ixp_network=None
    )

    IPInfo_Prefix.create_from_ipdbinfo(ipdb_info)

    prefixes = IPInfo_Prefix.select()
    assert len(prefixes) == 1

    prefix = prefixes[0]
    assert prefix.prefix == ipaddress.ip_network("192.0.2.0/24")
    assert prefix.origins == [(65511, "test 2")]
    assert prefix.ixp_network is None

    origins = IPInfo_Origin.select()
    assert len(origins) == 1

    ipx_networks = IPInfo_IXPNetwork.select()
    assert len(ipx_networks) == 0

    assert prefix.to_ipdbinfo() == ipdb_info


def test_ip_info_db_remove_old_entries(db):
    """Create two records, expire one of them and get it removed."""

    ipdb_info_1 = IPDBInfo(
        prefix=ipaddress.ip_network("192.0.2.0/25"),
        origins=[
            (65501, "test 1 a"),
            (65502, "test 1 b")
        ],
        ixp_network=None
    )

    ipdb_info_2 = IPDBInfo(
        prefix=ipaddress.ip_network("192.0.2.128/25"),
        origins=[
            (65511, "test 2")
        ],
        ixp_network=None
    )

    prefix_1 = IPInfo_Prefix.create_from_ipdbinfo(ipdb_info_1)
    IPInfo_Prefix.create_from_ipdbinfo(ipdb_info_2)

    prefixes = IPInfo_Prefix.select()
    assert len(prefixes) == 2

    origins = IPInfo_Origin.select()
    assert len(origins) == 3

    # Let's move the last_updated of one of the
    # prefix back 1 year, so that it will be
    # taken into account by the function tha removes
    # the old entries.
    prefix_1.last_updated = datetime.datetime.utcnow() - datetime.timedelta(days=365)
    prefix_1.save()

    remove_old_entries()

    # Only 1 prefix with 1 origin should be left now,
    # those linked to ipdb_info_2.

    prefixes = IPInfo_Prefix.select()
    assert len(prefixes) == 1

    origins = IPInfo_Origin.select()
    assert len(origins) == 1
