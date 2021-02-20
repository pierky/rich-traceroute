from __future__ import annotations
from typing import Optional, List, Tuple
import datetime
import ipaddress

from peewee import (
    BigIntegerField,
    DateTimeField,
    CharField,
    ForeignKeyField
)

from ..db import BaseModel
from ..structures import IPDBInfo, IXPNetwork
from ..config import IP_INFO_EXPIRY


class IPPrefix(CharField):

    def db_value(self, value):
        return str(value)

    def python_value(self, value):
        return ipaddress.ip_network(value)


class IPInfo_Prefix(BaseModel):

    # 39, max len of a str representing an IPv6 addr.
    prefix = IPPrefix(primary_key=True, max_length=39)

    last_updated = DateTimeField(default=datetime.datetime.utcnow)

    def to_ipdbinfo(self) -> IPDBInfo:
        ixp_network: Optional[IXPNetwork]
        origins: Optional[List[Tuple[int, str]]]

        if self.ixp_network:
            ixp_network = IXPNetwork(
                lan_name=self.ixp_network.lan_name,
                ix_name=self.ixp_network.ix_name,
                ix_description=self.ixp_network.ix_description
            )
        else:
            ixp_network = None

        if self.origins:
            origins = [
                (int(origin.asn), str(origin.holder))
                for origin in self.origins  # pylint: disable=no-member
            ]
        else:
            origins = None

        return IPDBInfo(
            prefix=self.prefix,
            origins=origins,
            ixp_network=ixp_network
        )

    @property
    def ixp_network(self):
        # pylint: disable=no-member
        if self._ixp_network:
            return self._ixp_network[0]

        return None

    @property
    def origins(self):
        # pylint: disable=no-member
        if self._origins:
            return self._origins

        return None

    @staticmethod
    def create_from_ipdbinfo(ipdb_info: IPDBInfo) -> IPInfo_Prefix:
        prefix, created = IPInfo_Prefix.get_or_create(
            prefix=ipdb_info.prefix
        )

        if not created:
            prefix.last_updated = datetime.datetime.utcnow()
            prefix.save()

            IPInfo_Origin.delete().where(
                IPInfo_Origin.prefix == prefix
            ).execute()

            IPInfo_IXPNetwork.delete().where(
                IPInfo_IXPNetwork.prefix == prefix
            ).execute()

        for origin_asn, holder in ipdb_info.origins or []:
            IPInfo_Origin.create(
                prefix=prefix,
                asn=origin_asn,
                holder=holder
            )

        if ipdb_info.ixp_network:
            IPInfo_IXPNetwork.create(
                prefix=prefix,
                **ipdb_info.ixp_network._asdict()
            )

        return prefix


class IPInfo_Origin(BaseModel):

    prefix = ForeignKeyField(IPInfo_Prefix, backref="_origins",
                             on_delete="CASCADE")

    asn = BigIntegerField(null=False)
    holder = CharField(max_length=256)


class IPInfo_IXPNetwork(BaseModel):

    prefix = ForeignKeyField(IPInfo_Prefix,
                             primary_key=True,
                             backref="_ixp_network",
                             on_delete="CASCADE")

    lan_name = CharField(null=True)
    ix_name = CharField(null=True)
    ix_description = CharField(null=True)


def remove_old_entries(expiry: datetime.timedelta = IP_INFO_EXPIRY) -> None:
    IPInfo_Prefix.delete().where(
        IPInfo_Prefix.last_updated <= datetime.datetime.utcnow() - expiry
    ).execute()
