from typing import List
import ipaddress

from .line_by_line import LineByLineParser
from ...errors import ParserError


class WindowsTracertParser(LineByLineParser):

    DESCRIPTION = "Windows tracert"

    EXAMPLES = [
        "tests/data/traceroute/win_tracert_1.txt"
    ]

    def _build_internal_repr(self):
        lines = self.raw_data.splitlines()

        last_hop_n: int = 0
        this_hop_n: int

        for line in lines:
            if not line.strip():
                continue

            parts = line.split()

            if not parts:
                continue

            hop_n_raw = parts[0]
            if not hop_n_raw.isdigit():
                continue

            this_hop_n = int(hop_n_raw)

            if this_hop_n != last_hop_n + 1:
                raise ParserError(
                    f"Unexpected hop n.: found {this_hop_n}, "
                    f"previous was {last_hop_n}"
                )

            # Extract IP address and latencies from the line
            rtts: List[float] = []
            missing_replies = 0

            # Multiple IP (and their replies) can be found on
            # the same line:
            # 5  185.235.236.4 (185.235.236.4)  1.620 ms  1.228 ms
            #    185.235.236.8 (185.235.236.8)  1.606 ms
            # (same line)
            for part in parts[1:]:
                val = part.replace(
                    "[", ""
                ).replace(
                    "]", ""
                ).replace(
                    "^C", ""
                ).strip()

                if val == "ms":
                    continue

                elif val == "*":
                    missing_replies += 1
                    continue

                else:

                    try:
                        ip = ipaddress.ip_address(val)

                        if not rtts:
                            raise ParserError(
                                f"Error while parsing line {line}: "
                                f"IP {ip} was found, but no RTTs were "
                                "gathered."
                            )

                        self._add_host_info(
                            this_hop_n,
                            (ip, rtts)
                        )

                        rtts = []

                        continue
                    except:  # noqa: E722
                        pass

                    try:
                        if part == "<1":
                            rtt = 0
                        else:
                            rtt = float(val)

                        rtts.append(rtt)

                        continue
                    except:  # noqa: E722
                        pass

            if rtts:
                rtts_text = " ".join(map(str, rtts))
                raise ParserError(
                    "Some RTTs were found "
                    f"({rtts_text}) but no IP "
                    "address is associated with them."
                )

            if missing_replies and not rtts:
                self._add_host_info(this_hop_n, None)

            last_hop_n = this_hop_n
