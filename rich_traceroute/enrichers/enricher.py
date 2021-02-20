from typing import Union, Optional, Tuple
import ipaddress
import threading
import queue
import logging
import requests
import datetime
import random

import radix
import markus
from flask_socketio import SocketIO


from .dns import name_to_ip, ip_to_name
from .dispatcher import dispatch_ipinfo
from ..traceroute import Host, HostOrigins, HostIXPNetwork, Traceroute
from ..ip_info_db import IPInfo_Prefix
from ..structures import IPDBInfo, EnricherJob, EnricherJob_Host
from ..metrics import get_tags, log_execution_time
from ..config import (
    IP_INFO_EXPIRY,
    SOCKET_IO_DATA_EVENT,
    SOCKET_IO_ERROR_EVENT,
    SOCKET_IO_ENRICHMENT_COMPLETED_EVENT,
    get_rabbitmq_url
)


LOGGER = logging.getLogger(__name__)
METRICS = markus.get_metrics(__name__)


class Enricher(threading.Thread):

    def __init__(self, name: str, queue: queue.Queue):
        super().__init__(name=name)

        self.daemon = True

        self.queue = queue

        # IP Info DB
        # -------------------------------------

        self.ip_info_db = radix.Radix()
        self.ip_info_db_lock = threading.Lock()

        # SocketIO
        # -------------------------------------

        self.socketio = SocketIO(
            message_queue=get_rabbitmq_url()
        )

        # Requests
        # -------------------------------------

        self.request_session = requests.Session()

    def _add_ip_info_to_db(self, ip_info: IPDBInfo) -> None:
        try:
            IPInfo_Prefix.create_from_ipdbinfo(ip_info)
        except:  # noqa: E722
            LOGGER.exception(
                "Unhandled exception while creating the ip_info "
                f"DB record for {ip_info.prefix}"
            )

    def add_ip_info_to_local_cache(
        self,
        ip_info: IPDBInfo,
        dispatch_to_others: bool,
        last_updated: datetime.datetime = datetime.datetime.utcnow()
    ) -> None:
        # This function is called from other threads too,
        # so make sure that it runs fast and it takes care
        # of locking the resources that it updates (the
        # ip_info_db specifically).

        with self.ip_info_db_lock:
            node = self.ip_info_db.add(str(ip_info.prefix))
            node.data["ip_db_info"] = ip_info
            node.data["last_updated"] = last_updated

        if dispatch_to_others:
            LOGGER.debug(
                f"Dispatching DB info to other threads: {ip_info.prefix}"
            )

            dispatch_ipinfo(ip_info)

    def _get_ip_info_from_db(self, ip: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]) -> Optional[IPDBInfo]:
        try:
            with self.ip_info_db_lock:
                node = self.ip_info_db.search_best(str(ip))
        except:  # noqa: E722
            LOGGER.exception(f"Lookup of {ip} failed")

        if node:
            # If the cached entry is expired, let's remove it.
            if node.data["last_updated"] < datetime.datetime.utcnow() - IP_INFO_EXPIRY:
                with self.ip_info_db_lock:
                    self.ip_info_db.delete(node.prefix)
                return None

            return node.data["ip_db_info"]

        return None

    @staticmethod
    def _get_hostname_from_ip(
        ip: Union[ipaddress.IPv4Network, ipaddress.IPv6Network]
    ) -> Optional[str]:

        try:
            METRICS.incr("ip_to_name", tags=get_tags())

            with log_execution_time(METRICS, LOGGER, "ip_to_name", str(ip)):
                return ip_to_name(str(ip))
        except:  # noqa E722
            return None

    @staticmethod
    def _get_ip_from_hostname(
        fqdn: str
    ) -> Optional[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]]:

        try:
            METRICS.incr("name_to_ip", tags=get_tags())

            with log_execution_time(METRICS, LOGGER, "name_to_ip", fqdn):
                ip = name_to_ip(fqdn)
            return ipaddress.ip_address(ip)
        except:  # noqa E722
            return None

    def _ripe_stat_query(self, url):
        return self.request_session.get(url)

    def _get_ip_info_from_external_sources(
        self,
        ip: Union[ipaddress.IPv4Network, ipaddress.IPv6Network]
    ) -> Optional[IPDBInfo]:

        METRICS.incr("ip_info_from_external_sources", tags=get_tags())

        with log_execution_time(METRICS, LOGGER, "ripestat.query_time", str(ip)):
            try:
                ripe_stat_response = self._ripe_stat_query(
                    f"https://stat.ripe.net/data/prefix-overview/data.json?resource={ip}"
                )
            except:  # noqa: E722
                LOGGER.exception(
                    f"RIPEstat query for {ip} failed."
                )
                METRICS.incr("ripestat.http_errors", tags=get_tags())
                return None

        try:
            ripe_stat_response.raise_for_status()
        except:  # noqa: E722
            LOGGER.exception(
                f"RIPEstat query for {ip} failed."
            )
            METRICS.incr("ripestat.http_errors", tags=get_tags())
            return None

        ripe_data = ripe_stat_response.json()

        if ripe_data["status"] != "ok":
            LOGGER.error(
                f"RIPEstat query for {ip} returned an error: "
                f"status is {ripe_data['status']}."
            )
            METRICS.incr("ripestat.query_errors", tags=get_tags())
            return None

        prefix = ipaddress.ip_network(ripe_data["data"]["resource"])

        origins = [
            (int(origin["asn"]), origin["holder"])
            for origin in ripe_data["data"]["asns"]
        ]

        return IPDBInfo(prefix, origins, None)

    def emit_host_enriched_event(
        self,
        traceroute_id: str,
        host: Host
    ) -> None:

        self.socketio.emit(
            SOCKET_IO_DATA_EVENT,
            {
                "traceroute_id": traceroute_id,
                **host.to_dict()
            },
            namespace=f"/t/{traceroute_id}"
        )

    def emit_host_enrichment_error_event(
        self,
        traceroute_id: str,
        hop_n: int,
        host_id: str,
        error: str
    ) -> None:
        self.socketio.emit(
            SOCKET_IO_ERROR_EVENT,
            {
                "traceroute_id": traceroute_id,
                "hop_n": hop_n,
                "host_id": host_id,
                "error": error
            },
            namespace=f"/t/{traceroute_id}"
        )

    def emit_enrichment_completed_event(
        self,
        traceroute: Traceroute
    ) -> None:
        self.socketio.emit(
            SOCKET_IO_ENRICHMENT_COMPLETED_EVENT,
            {
                "traceroute_id": traceroute.id,
                "traceroute": traceroute.to_dict(),
                "text": traceroute.to_text()
            },
            namespace=f"/t/{traceroute.id}"
        )

    def _enrich_host(self, traceroute_id: str, host: EnricherJob_Host) -> Tuple[Host, Optional[IPDBInfo]]:
        host_ip = None
        host_name = None
        ip_info = None

        try:
            host_ip = ipaddress.ip_address(host.host)
        except:  # noqa: E722
            host_name = host.host

        if host_ip:
            if host_ip.is_global:
                host_name = self._get_hostname_from_ip(host_ip)
        else:
            if host_name:
                host_ip = self._get_ip_from_hostname(host_name)

        if host_ip and host_ip.is_global:
            ip_info = self._get_ip_info_from_db(host_ip)

            if not ip_info:
                LOGGER.debug(f"IP info for {host_ip} not found; gathering them")

                ip_info = self._get_ip_info_from_external_sources(host_ip)

                if ip_info:
                    self.add_ip_info_to_local_cache(ip_info, True)
                    self._add_ip_info_to_db(ip_info)
            else:
                LOGGER.debug(f"IP info for {host_ip} found in the cache")

            LOGGER.debug(f"Host Data: {host_ip} / {host_name} / {ip_info}")

        db_host = Host.get(
            Host.id == host.host_id
        )
        db_host.ip = host_ip
        db_host.name = host_name
        db_host.enriched = True
        db_host.save()

        if ip_info:
            for asn, holder in ip_info.origins or []:
                HostOrigins.create(
                    host_id=host.host_id,
                    asn=asn,
                    holder=holder
                )

            if ip_info.ixp_network:
                HostIXPNetwork.create(
                    host_id=host.host_id,
                    lan_name=ip_info.ixp_network.lan_name,
                    ix_name=ip_info.ixp_network.ix_name,
                    ix_description=ip_info.ixp_network.ix_description
                )

        return db_host, ip_info

    def process_traceroute_enrichment_job(self, job: EnricherJob) -> Traceroute:
        traceroute = Traceroute.get(Traceroute.id == job.traceroute_id)
        traceroute.enrichment_started = datetime.datetime.utcnow()
        traceroute.save()

        for host in job.hosts:
            try:
                with log_execution_time(METRICS, LOGGER, "_enrich_host", host.host):
                    db_host, ip_info = self._enrich_host(job.traceroute_id, host)
            except:  # noqa: E722
                LOGGER.exception(
                    "Unhandled exception while enriching host ID "
                    f"{host.host_id} for hop n. {host.hop_n} of "
                    f"traceroute {job.traceroute_id}"
                )

                METRICS.incr("enrich_host.exceptions", tags=get_tags())

                self.emit_host_enrichment_error_event(
                    job.traceroute_id,
                    host.hop_n,
                    host.host_id,
                    "An error occurred while enriching "
                    "the information for this host."
                )
                continue

            try:
                self.emit_host_enriched_event(
                    job.traceroute_id,
                    db_host
                )
            except:  # noqa: E722
                LOGGER.exception(
                    "Unhandled exception while emitting SocketIO "
                    f"event for traceroute {job.traceroute_id}, hop n. "
                    f"{host.hop_n}, host_id {host.host_id}"
                )

        traceroute = Traceroute.get(Traceroute.id == job.traceroute_id)
        traceroute.enriched = True
        traceroute.enrichment_completed = datetime.datetime.utcnow()
        traceroute.save()

        self.emit_enrichment_completed_event(traceroute)

        return traceroute

    def _load_ip_info_entries_from_db(self):
        # Load entries from the DB
        LOGGER.info("Loading IP info entries from DB...")

        with log_execution_time(METRICS, LOGGER, "load_ip_info_entries_from_db"):
            for db_prefix in IPInfo_Prefix.select():
                self.add_ip_info_to_local_cache(
                    db_prefix.to_ipdbinfo(),
                    last_updated=db_prefix.last_updated,
                    dispatch_to_others=False
                )

        LOGGER.info("IP info entries loaded")

    def run(self):
        # Run the function that loads the existing IPInfo
        # entries from the DB in the next couple of minutes.
        # The loading of those entries would block the
        # thread, so let's do it asynchronously.
        delay = random.randrange(1, 120)
        thread = threading.Timer(delay, self._load_ip_info_entries_from_db)
        thread.name = self.name + "-load-entries-from-db"
        thread.start()

        LOGGER.info("Enricher ready to process jobs")
        while True:
            job = self.queue.get(block=True)

            if job is None:
                return

            try:
                self.process_traceroute_enrichment_job(job)
            except:  # noqa: E722
                LOGGER.exception("Unhandled exception while processing the job "
                                 f"{job.to_json_dict()}")

    def stop(self):
        self.queue.put(None)
