from typing import List, Optional
import ipaddress
import logging
import threading

import requests
import markus
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


from .consumer import ConsumerThread
from ..config import IXP_NETWORKS_UPDATE_INTERVAL
from ..structures import IPDBInfo, IXPNetwork
from ..ip_info_db import IPInfo_Prefix
from ..metrics import log_execution_time, get_tags


PEERINGDB_API_IXPFX = "https://www.peeringdb.com/api/ixpfx"
PEERINGDB_API_IXLAN = "https://www.peeringdb.com/api/ixlan"
PEERINGDB_API_IX = "https://www.peeringdb.com/api/ix"

LOGGER = logging.getLogger(__name__)
METRICS = markus.get_metrics(__name__)

thread = None


class PeeringDB:

    def __init__(self):
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT",
                             "DELETE", "OPTIONS", "TRACE"],
            backoff_factor=3
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)

        self.http_session = requests.Session()
        self.http_session.mount("https://", adapter)
        self.http_session.mount("http://", adapter)

    def _get(self, url: str):
        return self.http_session.get(
            url,
            timeout=30
        )

    def query(self, url: str) -> List[dict]:
        try:
            response = self._get(url)
        except:  # noqa: E722
            LOGGER.exception(
                f"PeeringDB query for {url} failed."
            )
            METRICS.incr("peeringdb.http_errors", tags=get_tags())
            return []

        try:
            response.raise_for_status()
        except:  # noqa: E722
            LOGGER.exception(
                f"PeeringDB query for {url} failed."
            )
            METRICS.incr("peeringdb.http_errors", tags=get_tags())
            return []

        return response.json()["data"]


class IXPNetworksUpdater:

    def __init__(self, consumers: List[ConsumerThread] = []):
        self.consumers = consumers

    @staticmethod
    def _lookup_ix_lans(ixlan_data: List[dict], ix_id: int) -> List[dict]:
        res = []

        for lan in ixlan_data:
            if lan["ix_id"] == ix_id:
                res.append(lan)

        return res

    @staticmethod
    def _lookup_ix_lan_prefixes(ix_prefixes_data: List[dict], ix_lan_id: int) -> List[dict]:
        res = []

        for prefix in ix_prefixes_data:
            if prefix["ixlan_id"] == ix_lan_id:
                res.append(prefix)

        return res

    def update_ixp_networks(self) -> None:
        with log_execution_time(METRICS, LOGGER, "_build_ixp_networks"):
            self._build_ixp_networks()

    def _dispatch_ip_info(self, ip_info: IPDBInfo) -> None:
        for consumer in self.consumers:
            for enricher in consumer.enrichers:
                enricher.add_ip_info_to_local_cache(ip_info, False)

    def _save_ip_info_to_db(self, ip_info: IPDBInfo) -> None:
        try:
            IPInfo_Prefix.create_from_ipdbinfo(ip_info)
        except:  # noqa: E722
            LOGGER.exception(
                "Unhandled exception while creating the ip_info "
                f"DB record for {ip_info.prefix}"
            )

    @staticmethod
    def _peeringdb_query(http_session, url) -> List[dict]:
        return http_session.get(url, timeout=30).json()["data"]

    def _build_ixp_networks(self):

        pdb = PeeringDB()

        with log_execution_time(METRICS, LOGGER, "peeringdb.pdb_ix_data"):
            pdb_ix_data: List[dict] = pdb.query(PEERINGDB_API_IX)

        with log_execution_time(METRICS, LOGGER, "peeringdb.pdb_ixlan_data"):
            pdb_ixlan_data: List[dict] = pdb.query(PEERINGDB_API_IXLAN)

        with log_execution_time(METRICS, LOGGER, "peeringdb.pdb_ix_prefixes"):
            pdb_ix_prefixes: List[dict] = pdb.query(PEERINGDB_API_IXPFX)

        ix_lan_cnt = 0

        for ix in pdb_ix_data:
            ix_id: int = int(ix["id"])
            ix_name: Optional[str] = ix["name"] or None
            ix_description: Optional[str] = ix["name_long"] or None

            ix_lans = self._lookup_ix_lans(pdb_ixlan_data, ix_id)

            for ix_lan in ix_lans:
                ix_lan_cnt += 1

                ix_lan_id: int = int(ix_lan["id"])
                ix_lan_name: Optional[str] = ix_lan["name"] or None

                ix_lan_prefixes = self._lookup_ix_lan_prefixes(pdb_ix_prefixes, ix_lan_id)

                for ix_prefix in ix_lan_prefixes:
                    prefix = ipaddress.ip_network(ix_prefix["prefix"])

                    ip_info = IPDBInfo(
                        prefix=prefix,
                        origins=None,
                        ixp_network=IXPNetwork(
                            lan_name=ix_lan_name,
                            ix_name=ix_name,
                            ix_description=ix_description
                        )
                    )

                    self._save_ip_info_to_db(ip_info)

                    try:
                        self._dispatch_ip_info(ip_info)
                    except:  # noqa: E722
                        LOGGER.exception(
                            "Unhandled exception while dispatching the ip_info "
                            f"record for {ip_info.prefix}. Aborting the execution "
                            "of IXPNetworksUpdater"
                        )
                        return

                if ix_lan_cnt % 100 == 0:
                    LOGGER.info(f"{ix_lan_cnt} IXP networks processed")

        LOGGER.info(f"{ix_lan_cnt} IXP networks processed")


def setup_ixp_networks_updater(consumers: List[ConsumerThread]):

    def _setup_thread(interval: int):
        global thread
        thread = threading.Timer(interval, _run_updater)
        thread.name = "IXPNetworksUpdater"
        thread.start()

    def _run_updater():
        try:
            LOGGER.info("Running the IXP networks updater")
            updater = IXPNetworksUpdater(consumers)
            updater.update_ixp_networks()
            LOGGER.info("IXP networks updater completed")
        except:  # noqa: E722
            LOGGER.exception(
                "Unhandled exception while updating IXP networks"
            )

        _setup_thread(IXP_NETWORKS_UPDATE_INTERVAL)

    _setup_thread(IXP_NETWORKS_UPDATE_INTERVAL)


def teardown_ixp_networks_updater() -> None:
    global thread
    if thread:
        thread.cancel()
        thread = None
