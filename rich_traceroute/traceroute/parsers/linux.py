from typing import List
import ipaddress

from .line_by_line import LineByLineParser, IPAddress
from ...errors import ParserError


class LinuxParser(LineByLineParser):

    DESCRIPTION = "Linux-like traceroute format"

    EXAMPLES = [
        "tests/data/traceroute/linux_1.txt"
    ]

    def _build_internal_repr(self):
        lines = self.raw_data.splitlines()

        last_hop_n: int = 0
        this_hop_n: int

        for line in lines:
            if not line.strip():
                continue

            if line.startswith(("traceroute to ", "traceroute6 to ")):
                continue

            parts = line.split()

            if not parts:
                continue

            hop_n_raw = parts[0]
            if not hop_n_raw.isdigit():
                continue

            this_hop_n = int(hop_n_raw)

            if this_hop_n == 0:
                continue

            if this_hop_n not in (last_hop_n, last_hop_n + 1):
                raise ParserError(
                    f"Unexpected hop n.: found {this_hop_n}, "
                    f"previous was {last_hop_n}"
                )

            parts = parts[1:]

            # Extract IP address and latencies from the line
            last_ip: IPAddress
            ip_found = False
            hostname: str = None
            hostname_found = False
            rtts: List[float] = []
            missing_replies = 0

            # Multiple IP (and their replies) can be found on
            # the same line:
            # 5  185.235.236.4 (185.235.236.4)  1.620 ms  1.228 ms
            #    185.235.236.8 (185.235.236.8)  1.606 ms
            # (same line)
            for part in parts:
                val = part.replace(
                    "(", ""
                ).replace(
                    ")", ""
                ).replace(
                    "^C", ""
                ).strip()

                if val == "ms":
                    continue

                if val == "*":
                    missing_replies += 1
                    continue

                try:
                    last_ip = ipaddress.ip_address(val)

                    ip_found = True

                    continue
                except:  # noqa: E722
                    pass

                try:
                    rtt = self.extract_rtt_from_str(val)

                    rtts.append(rtt)

                    if not ip_found and not hostname_found:
                        raise ParserError(
                            f"RTT {rtt} found, but last host not "
                            "determined."
                        )

                    if ip_found:
                        self._add_host_info(
                            this_hop_n,
                            (last_ip, [rtt])
                        )
                    elif hostname_found:
                        self._add_host_info(
                            this_hop_n,
                            (hostname, [rtt])
                        )

                    continue
                except:  # noqa: E722
                    # If it's not an IP and it's not a RTT, it could
                    # be a hostname.

                    if self.looks_like_a_hostname(val) and not hostname_found:
                        hostname = val

                        hostname_found = True

                        continue

            if ip_found:
                if not rtts and not missing_replies:
                    raise ParserError(
                        f"IP {last_ip} was found while parsing {line} but with "
                        "no missing replies nor RTT values"
                    )
            elif hostname_found:
                if not rtts and not missing_replies:
                    raise ParserError(
                        f"Host {hostname} was found while parsing {line} but with "
                        "no missing replies nor RTT values"
                    )
            else:
                if not missing_replies:
                    raise ParserError(
                        f"No IP was found while parsing line {line}, but "
                        "also no missing replies were found"
                    )
                else:
                    self._add_host_info(this_hop_n, None)

            last_hop_n = this_hop_n
