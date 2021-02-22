from typing import List
import ipaddress

from .line_by_line import LineByLineParser, IPAddress
from ...errors import ParserError


class BSDParser(LineByLineParser):

    DESCRIPTION = "BSD-like traceroute format"

    EXAMPLES = [
        "tests/data/traceroute/bsd_4.txt"
    ]

    def _build_internal_repr(self):
        lines = self.raw_data.splitlines()

        last_hop_n: int = 0
        this_hop_n: int

        for line in lines:
            if not line.strip():
                continue

            if line.startswith("traceroute to "):
                continue

            # beginning_of_line represents the first colum:
            #  4  10.254.0.217 (10.254.0.217)  15.234 ms  15.081 ms
            #     10.254.0.221 (10.254.0.221)  13.549 ms
            # ^^^
            beginning_of_line = line[0:3].strip()

            if beginning_of_line and beginning_of_line.isdigit():
                this_hop_n = int(beginning_of_line)

                if this_hop_n == 0:
                    continue

                if this_hop_n != last_hop_n + 1:
                    raise ParserError(
                        f"Unexpected hop n.: found {this_hop_n}, "
                        f"previous was {last_hop_n}"
                    )

            else:
                this_hop_n = last_hop_n

            cols = line[3:].split()

            # Extract IP address and latencies from the line
            ip: IPAddress
            ip_found = False
            rtts: List[float] = []
            missing_replies = 0

            for col in cols:
                val = col.replace(
                    "(", ""
                ).replace(
                    ")", ""
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
                        ip_found = True
                        continue
                    except:  # noqa: E722
                        pass

                    try:
                        rtt = self.extract_rtt_from_str(val)
                        rtts.append(rtt)
                        continue
                    except:  # noqa: E722
                        pass

            if this_hop_n > 0:
                if ip_found:
                    if not rtts and not missing_replies:
                        raise ParserError(
                            f"IP {ip} was found while parsing {line} but with "
                            "no missing replies nor RTT values"
                        )
                else:
                    if not missing_replies:
                        raise ParserError(
                            f"No IP was found while parsing line {line}, but "
                            "also no missing replies were found"
                        )

                if ip_found:
                    self._add_host_info(this_hop_n, (ip, rtts))
                else:
                    self._add_host_info(this_hop_n, None)

                last_hop_n = this_hop_n
