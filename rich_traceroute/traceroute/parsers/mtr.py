from typing import Union, Tuple

from .base import BaseParser, HopHost
from ...errors import ParserError


class MTRParser(BaseParser):

    DESCRIPTION = "MTR plain text"

    EXAMPLES = [
        "tests/data/traceroute/mtr_2.txt"
    ]

    def _add_hop_host(self, hop_n: int, host: Union[str, None], **host_attrs) -> None:
        if hop_n not in self.hops:
            self.hops[hop_n] = []

        if host:
            self.hops[hop_n].append(
                HopHost(
                    host=host,
                    **host_attrs
                )
            )

    @staticmethod
    def _get_hop_n(line: str) -> Tuple[int, str]:

        #  1.|-- 192.168.1.254              0.0%     2    3.8   6.4   3.8   9.1   3.7
        #  2.|-- 10.1.131.181               0.0%     2    9.0   9.2   9.0   9.5   0.4

        if "|--" not in line:
            raise ParserError("'|--' marker not found")

        raw_hop_n = line.split("|--")[0].strip()[:-1]

        if not raw_hop_n.isdigit():
            raise ParserError(f"the parsed hop is not numeric: {raw_hop_n}")

        return int(raw_hop_n), line.split("|--")[1].strip()

    def _parse(self):
        lines = self.raw_data.splitlines()

        processing_hops = False

        for line in lines:
            if line.startswith("HOST:"):
                # HOST: localhost                   Loss%   Snt   Last   Avg  Best  Wrst StDev
                processing_hops = True
                continue

            if line.startswith("Host"):
                # Host              Loss%   Snt   Last   Avg  Best  Wrst StDev
                processing_hops = True
                continue

            if not processing_hops:
                continue

            #  1.|-- 192.168.1.254              0.0%     2    3.8   6.4   3.8   9.1   3.7
            #  2.|-- 10.1.131.181               0.0%     2    9.0   9.2   9.0   9.5   0.4

            this_hop_n, line_info = self._get_hop_n(line)

            fields = line_info.split()

            # Parsing the host
            # --------------------------

            # "192.168.1.254", "???"
            host = fields[0]

            if "?" in host:
                self._add_hop_host(this_hop_n, None)

                continue

            # Parsing the attributes
            # --------------------------

            host_attrs = {}

            # Parsing the loss
            # --------------------------

            raw_loss = fields[1].replace("%", "")

            # Check if raw_loss represents a float.
            # Replace only one occurrence of "." with a blank, then check
            # if the resulting string is all digits.
            if not raw_loss.replace(".", "", 1).isdigit():
                raise ParserError(f"can't parse the loss value {raw_loss}, "
                                  f"it doesn't look like a float")

            host_attrs["loss"] = float(raw_loss)

            # Parsing the RTTs
            # --------------------------

            for what_we_are_parsing, field_idx in [
                ("avg_rtt", 4),
                ("min_rtt", 5),
                ("max_rtt", 6)
            ]:

                raw_rtt = fields[field_idx]

                # Check if raw_rtt represents a float.
                # Replace only one occurrence of "." with a blank, then check
                # if the resulting string is all digits.
                if not raw_rtt.replace(".", "", 1).isdigit():
                    raise ParserError(f"can't parse the {what_we_are_parsing} RTT value {raw_rtt}, "
                                      f"it doesn't look like a float")

                rtt = float(raw_rtt)

                host_attrs[what_we_are_parsing] = rtt

            self._add_hop_host(this_hop_n, host, **host_attrs)
