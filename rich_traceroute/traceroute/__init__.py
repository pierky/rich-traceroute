from __future__ import annotations
import logging
import datetime
import uuid
import hashlib
import json
import textwrap
import ipaddress

from peewee import (
    AutoField,
    DateTimeField,
    CharField,
    BooleanField,
    ForeignKeyField,
    IntegerField,
    DecimalField
)

from ..db import BaseModel
from ..enrichers.dispatcher import dispatch_traceroute_enrichment_job
from ..structures import EnricherJob, EnricherJob_Host
from ..config import MAX_ENRICHMENT_TIME
from .parsers import parse_raw_traceroute

logger = logging.getLogger(__name__)


def record_uid() -> str:
    buff = str(uuid.uuid4())
    m = hashlib.sha1()
    m.update(buff.encode())
    return m.hexdigest()


class Traceroute(BaseModel):

    id = CharField(primary_key=True, default=record_uid)

    raw = CharField(max_length=1024 * 16)
    created = DateTimeField(default=datetime.datetime.utcnow)

    parsed = BooleanField(default=False)
    enriched = BooleanField(default=False)
    enrichment_started = DateTimeField(null=True)
    enrichment_completed = DateTimeField(null=True)

    last_seen = DateTimeField(default=datetime.datetime.utcnow)

    def parse(self):
        parser = parse_raw_traceroute(self.raw)

        if not parser:
            return

        for hop_n, hosts in parser.hops.items():
            hop = Hop(traceroute=self, hop_number=hop_n)
            hop.save()

            for host in hosts:
                Host.create(
                    hop=hop,
                    original_host=host.host,
                    avg_rtt=host.avg_rtt,
                    min_rtt=host.min_rtt,
                    max_rtt=host.max_rtt,
                    loss=host.loss
                )

        self.parsed = True
        self.save()
        self.dispatch_to_enrichers()

    def dispatch_to_enrichers(self):
        hosts = []
        for hop in self.hops:  # pylint: disable=no-member
            for host in hop.hosts:
                hosts.append(EnricherJob_Host(
                    hop.hop_number,
                    host.id,
                    host.original_host
                ))

        job = EnricherJob(traceroute_id=self.id, hosts=hosts)

        dispatch_traceroute_enrichment_job(job)

    def get_hop_n(self, hop_n: int) -> Hop:
        for hop in self.hops:  # pylint: disable=no-member
            if hop.hop_number == hop_n:
                return hop

        raise ValueError(
            f"Hop n. {hop_n} not found in traceroute {self.id}"
        )

    @property
    def status(self):
        if not self.parsed:
            return "not_parsed"

        if self.enriched:
            return "enriched"

        if self.created < datetime.datetime.utcnow() - MAX_ENRICHMENT_TIME:
            return "timeout"

        return "wip"

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):

        return {
            "id": self.id,
            "status": self.status,
            "enriched": self.enriched,
            "parsed": self.parsed,

            "hops": {
                hop.hop_number: [
                    host.to_dict()
                    for host in hop.hosts
                ]
                for hop in self.hops  # pylint: disable=no-member
            }
        }

    def to_text(self) -> str:
        res = ""

        # Determining which attributes should be used in the output.
        has_loss = False
        has_rtt = False
        max_ip_len = 0

        for hop in self.hops:  # pylint: disable=no-member
            for host in hop.hosts:
                if host.loss is not None:
                    has_loss = True

                if host.avg_rtt:
                    has_rtt = True

                max_ip_len = max(max_ip_len, len(str(host.ip)))

        # Preparing the template to be used to print each hop host.
        tpl_leftmost_side = "{this_hop_txt: >4} {host: <" + str(max_ip_len + 2) + "}"

        tpl_head = tpl_leftmost_side
        tpl_host = tpl_leftmost_side

        if has_loss:
            tpl_head += " {loss:>4}"
            tpl_host += " {loss:>3}%"

        if has_rtt:
            if has_loss:
                tpl_head += "  "
                tpl_host += "  "

            tpl_head += "{rtt:>10}"
            tpl_host += "{rtt:>7} ms"

        MAX_LEN_FOR_IP_DETAILS = 25

        tpl_head += "   {origin:8} {holder:" + str(MAX_LEN_FOR_IP_DETAILS) + "}   {name}"
        tpl_orign = "   {origin:8} {holder:" + str(MAX_LEN_FOR_IP_DETAILS) + "}   {name}"
        tpl_ixlan = "   {ixp_network:" + str(MAX_LEN_FOR_IP_DETAILS + 9) + "}   {name}"

        res += tpl_head.format(
            this_hop_txt="Hop",
            host="IP",
            loss="Loss",
            rtt="RTT",
            origin="Origin",
            holder="",
            name="Reverse"
        ) + "\n"

        for hop in self.hops:  # pylint: disable=no-member
            if not hop.hosts:
                res += tpl_leftmost_side.format(
                    this_hop_txt=str(hop.hop_number) + ".",
                    host="*"
                ) + "\n"

                continue

            for host_idx, host in enumerate(
                sorted(hop.hosts, key=lambda h: h.ip or h.original_host)
            ):  # pylint: disable=no-member
                if host_idx == 0:
                    this_hop_txt = str(hop.hop_number) + "."
                else:
                    this_hop_txt = ""

                line = tpl_host.format(
                    this_hop_txt=this_hop_txt,
                    host=host.ip or host.original_host,
                    loss=int(round(host.loss)) if host.loss is not None else "",
                    rtt="{:>7.2f}".format(host.avg_rtt) if host.avg_rtt is not None else "",
                )

                res += line

                ip_info_line_n = 0

                for origin in host.origins:
                    ip_info_line_n += 1

                    if ip_info_line_n > 1:
                        res += "\n"
                        res += " " * len(line)

                    res += tpl_orign.format(
                        origin="AS{}".format(origin.asn),
                        holder=textwrap.shorten(
                            origin.holder,
                            width=MAX_LEN_FOR_IP_DETAILS,
                            placeholder="..."
                        ),
                        name=host.name if (host.name and ip_info_line_n == 1) else ""
                    )

                if host.ixp_network:
                    ip_info_line_n += 1

                    res += tpl_ixlan.format(
                        ixp_network=textwrap.shorten(
                            "IX: {}".format(host.ixp_network.ix_name),
                            width=MAX_LEN_FOR_IP_DETAILS,
                            placeholder="..."
                        ),
                        name=host.name if (host.name and ip_info_line_n == 1) else ""
                    )

                # If no origins nor ixp_network were found,
                # just print the reverse.
                if ip_info_line_n == 0 and host.name:
                    res += tpl_orign.format(
                        origin="",
                        holder="",
                        name=host.name
                    )

                res += "\n"

        return res


class Hop(BaseModel):

    id = AutoField()
    traceroute = ForeignKeyField(Traceroute, backref="hops")
    hop_number = IntegerField()


class Host(BaseModel):

    id = CharField(primary_key=True, default=record_uid)
    hop = ForeignKeyField(Hop, backref="hosts")

    original_host = CharField()
    avg_rtt = DecimalField(null=True, decimal_places=2)
    min_rtt = DecimalField(null=True, decimal_places=2)
    max_rtt = DecimalField(null=True, decimal_places=2)
    loss = DecimalField(null=True, decimal_places=2)

    ip = CharField(null=True)
    name = CharField(null=True)

    enriched = BooleanField(default=False)

    @property
    def ixp_network(self):
        # pylint: disable=no-member
        if self._ixp_networks:
            return self._ixp_networks[0]

        return None

    @property
    def is_global(self) -> bool:
        if self.ip:
            return ipaddress.ip_address(self.ip).is_global
        else:
            return False

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self) -> dict:

        def _float_or_none(v):
            if v is None:
                return None
            return float(v)

        return {
            "id": self.id,
            "hop_number": self.hop.hop_number,
            "original_host": self.original_host,
            "avg_rtt": _float_or_none(self.avg_rtt),
            "min_rtt": _float_or_none(self.min_rtt),
            "max_rtt": _float_or_none(self.max_rtt),
            "loss": _float_or_none(self.loss),
            "ip": str(self.ip) if self.ip else None,
            "is_global": self.is_global,
            "name": self.name if self.name else None,
            "enriched": self.enriched,
            "ixp_network": {
                "lan_name": self.ixp_network.lan_name,
                "ix_name": self.ixp_network.ix_name,
                "ix_description": self.ixp_network.ix_description,
            } if self.ixp_network else None,
            "origins": [
                (origin.asn, origin.holder)
                for origin in self.origins  # pylint: disable=no-member
            ] if self.origins else None  # pylint: disable=no-member
        }


class HostOrigins(BaseModel):

    host_id = ForeignKeyField(Host, backref="origins")

    asn = IntegerField(null=False)
    holder = CharField(null=False)


class HostIXPNetwork(BaseModel):

    host_id = ForeignKeyField(Host, primary_key=True, backref="_ixp_networks")

    lan_name = CharField(null=True)
    ix_name = CharField(null=True)
    ix_description = CharField(null=True)


def create_traceroute(raw_data) -> Traceroute:
    t = Traceroute.create(raw=raw_data)
    t.parse()
    return t
