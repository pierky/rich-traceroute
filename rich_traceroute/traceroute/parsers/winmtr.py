import ipaddress
from typing import Union

from .base import BaseParser, HopHost
from ...errors import ParserError


class WinMTRParser(BaseParser):

    DESCRIPTION = "WinMTR"

    EXAMPLES = [
        "tests/data/traceroute/winmtr_1.txt"
    ]

    def _add_hop_host(self, host: Union[str, None], **host_attrs) -> None:
        new_hop_n = len(self.hops.keys()) + 1
        self.hops[new_hop_n] = []

        if host:
            self.hops[new_hop_n].append(
                HopHost(
                    host=host,
                    **host_attrs
                )
            )

    def _parse(self):
        lines = self.raw_data.splitlines()

        # Set when 'WinMTR statistics' is found
        title_found = False

        processing_hops = False

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if "WinMTR statistics" in line:
                title_found = True
                continue

            if not title_found:
                continue

            if "----" in line:
                processing_hops = True
                continue

            if not processing_hops:
                continue

            if "____" in line:
                continue

            line = line.replace("|", "")
            line = line.replace("-", "")
            line = line.replace("No response from host", "?")
            parts = line.split()

            if len(parts) < 8:
                raise ParserError(
                    f"Was expecting to find 8 parts: {line}"
                )

            host = parts[0]

            if host == "?":
                self._add_hop_host(None)
                continue

            try:
                ipaddress.ip_address(host)
            except:  # noqa: E722
                if not self.looks_like_a_hostname(host):
                    raise ParserError(
                        f"Can't determine the host from line {line}"
                    )

            host_attrs_and_part_idx = [
                ("loss", 1),
                ("min_rtt", 4),
                ("avg_rtt", 5),
                ("max_rtt", 6)
            ]

            host_attrs = {}

            for attr, part_idx in host_attrs_and_part_idx:
                raw = parts[part_idx]
                try:
                    val = float(raw)
                except:  # noqa: E722
                    raise ParserError(
                        f"Can't convert {attr} from {raw}"
                    )

                host_attrs[attr] = val

            self._add_hop_host(host, **host_attrs)
