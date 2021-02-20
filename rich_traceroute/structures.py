from __future__ import annotations

from typing import NamedTuple, List, Union, Tuple, Optional
import ipaddress


class IXPNetwork(NamedTuple):

    lan_name: str
    ix_name: str
    ix_description: str


class IPDBInfo(NamedTuple):

    prefix: Union[ipaddress.IPv4Network, ipaddress.IPv6Network]
    origins: Optional[List[Tuple[int, str]]]
    ixp_network: Optional[IXPNetwork]

    def to_json_dict(self):
        if self.ixp_network:
            ixp_network_dict = self.ixp_network._asdict()
        else:
            ixp_network_dict = None

        return {
            "prefix": str(self.prefix),
            "origins": self.origins or None,
            "ixp_network": ixp_network_dict
        }

    @staticmethod
    def from_dict(dic: dict) -> IPDBInfo:
        assert "prefix" in dic
        assert "origins" in dic
        assert "ixp_network" in dic
        if dic["origins"]:
            assert isinstance(dic["origins"], list)
        if dic["ixp_network"]:
            assert isinstance(dic["ixp_network"], dict)

        ixp_network: Optional[IXPNetwork]
        origins: Optional[List[Tuple[int, str]]]

        if dic["ixp_network"]:
            ixp_network = IXPNetwork(**dic["ixp_network"])
        else:
            ixp_network = None

        if dic["origins"]:
            origins = [
                (int(origin[0]), str(origin[1]))
                for origin in dic["origins"]
            ]
        else:
            origins = None

        return IPDBInfo(
            prefix=ipaddress.ip_network(dic["prefix"]),
            origins=origins,
            ixp_network=ixp_network
        )


class EnricherJob_Host(NamedTuple):

    hop_n: int
    host_id: str
    host: str


class EnricherJob(NamedTuple):

    traceroute_id: str
    hosts: List[EnricherJob_Host]

    def to_json_dict(self):
        return {
            "traceroute_id": self.traceroute_id,
            "hosts": [
                host._asdict()
                for host in self.hosts
            ]
        }

    @staticmethod
    def from_dict(dic: dict) -> EnricherJob:
        assert "traceroute_id" in dic
        assert "hosts" in dic
        assert isinstance(dic["hosts"], list)

        hosts: List[EnricherJob_Host] = []
        for host in dic["hosts"]:
            hosts.append(EnricherJob_Host(**host))

        return EnricherJob(
            traceroute_id=dic["traceroute_id"],
            hosts=hosts
        )


def test_enricherjob_from_to_dict():
    raw = {
        "traceroute_id": "test1",
        "hosts": [
            {
                "hop_n": 1,
                "host_id": 1,
                "host": "1.2.3.4"
            },
            {
                "hop_n": 2,
                "host_id": 2,
                "host": "www.example.com"
            }
        ]
    }

    job = EnricherJob.from_dict(raw)

    assert job.hosts[0].host == "1.2.3.4"
    assert job.hosts[1].host == "www.example.com"

    assert job.to_json_dict() == raw


def test_ipdbinfo_from_json_dict():
    raw = {
        "prefix": "192.0.2.0/24",
        "origins": [[65500, "test 1"]],
        "ixp_network": {
            "lan_name": "test LAN name",
            "ix_name": "test name",
            "ix_description": "test description"
        }
    }

    ipdbinfo = IPDBInfo.from_dict(raw)

    assert ipdbinfo.prefix == ipaddress.IPv4Network("192.0.2.0/24")
    assert ipdbinfo.origins == [(65500, "test 1")]
    assert isinstance(ipdbinfo.ixp_network, IXPNetwork)
    assert ipdbinfo.ixp_network.lan_name == "test LAN name"
    assert ipdbinfo.ixp_network.ix_name == "test name"
    assert ipdbinfo.ixp_network.ix_description == "test description"
