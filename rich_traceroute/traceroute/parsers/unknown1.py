import ipaddress

from .line_by_line import LineByLineParser
from .base import OTHER_UNKNOWN_TRACEROUTE_FORMAT
from ...errors import ParserError


class UnknownFormat1Parser(LineByLineParser):

    DESCRIPTION = OTHER_UNKNOWN_TRACEROUTE_FORMAT

    EXAMPLES = [
        "tests/data/traceroute/unknown1_1.txt"
    ]

    def _build_internal_repr(self):
        lines = self.raw_data.splitlines()

        processing_hops = False

        last_hop_n: int = 0
        this_hop_n: int

        for line in lines:
            if not line.strip():
                continue

            parts = line.split()

            if not parts:
                continue

            hop_n_raw = parts[0].strip()

            if hop_n_raw == "1:":
                processing_hops = True

            if not processing_hops:
                continue

            if not hop_n_raw.endswith(":"):
                raise ParserError(
                    f"Hop n. does not end with ':': {hop_n_raw}"
                )

            this_hop_n = int(hop_n_raw[:-1])

            if this_hop_n not in (last_hop_n, last_hop_n + 1):
                raise ParserError(
                    f"Unexpected hop n.: found {this_hop_n}, "
                    f"previous was {last_hop_n}"
                )

            host = parts[1]

            try:
                ipaddress.ip_address(host)
            except:  # noqa: E722
                if not self.looks_like_a_hostname(host):
                    raise ParserError(
                        f"Can't determine the host from line {line}"
                    )

            rtt_raw = parts[2]

            if not rtt_raw.endswith("ms"):
                raise ParserError(
                    f"RTT does not end with 'ms': {rtt_raw}"
                )

            rtt_raw = rtt_raw[:-2]

            try:
                rtt = float(rtt_raw)
            except:  # noqa: E722
                raise ParserError(
                    f"Can't convert string '{rtt}' into float"
                )

            self._add_host_info(
                this_hop_n,
                (host, [rtt])
            )

            last_hop_n = this_hop_n
