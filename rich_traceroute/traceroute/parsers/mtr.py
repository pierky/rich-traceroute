from typing import Union, Tuple

from .base import BaseParser, HopHost
from ...errors import ParserError


class MTRParser(BaseParser):

    DESCRIPTION = "MTR (report mode)"

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

    def _add_host_to_previous_hop(self, host: str, hop_n: int) -> None:
        if hop_n == 0:
            raise ParserError(f"Additional host {host} found, but hop_n is zero")

        if not self.hops[hop_n]:
            raise ParserError(
                f"Additional host {host} found for hop {hop_n}, "
                "but no previous hosts found"
            )

        previous_hophost = self.hops[hop_n][0]

        self.hops[hop_n].append(
            HopHost(
                **{
                    **previous_hophost._asdict(),
                    **{"host": host}
                }
            )
        )

    @staticmethod
    def _get_hop_n(line: str) -> Tuple[int, str]:

        #  1.|-- 192.168.1.254      0.0%     2    3.8   6.4   3.8   9.1   3.7
        #  2.|-- 10.1.131.181       0.0%     2    9.0   9.2   9.0   9.5   0.4

        if "|--" not in line:
            raise ParserError("'|--' marker not found")

        raw_hop_n = line.split("|--")[0].strip()[:-1]

        if not raw_hop_n.isdigit():
            raise ParserError(f"the parsed hop is not numeric: {raw_hop_n}")

        return int(raw_hop_n), line.split("|--")[1].strip()

    def _parse(self):
        lines = self.raw_data.splitlines()

        processing_hops = False

        last_hop_n = 0

        for line in lines:
            line = line.replace("^C", "")

            # Lines which show additional hosts from which a reply
            # was received for the same hop that was previously
            # processed.
            #
            #  7. 192.168.8.129      0.0%  2357    0.2   1.1   0.1  45.3   3.7
            #     192.168.10.1
            #     192.168.9.65
            seems_to_be_a_continuation_line = line[:4].strip() == ""

            line = line.strip()

            if not line:
                continue

            if line.startswith("HOST:"):
                # HOST: localhost                   Loss%   Snt   Last   Avg  Best  Wrst StDev
                processing_hops = True
                continue

            if line.startswith("Host "):
                # Host              Loss%   Snt   Last   Avg  Best  Wrst StDev
                processing_hops = True
                continue

            if not processing_hops:
                continue

            line = line.replace("(waiting for reply)", "???")

            if seems_to_be_a_continuation_line:
                this_hop_n = last_hop_n

                fields = line.split()

                host = fields[0]

                self._add_host_to_previous_hop(host, this_hop_n)

                continue
            else:

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

            last_hop_n = this_hop_n

            self._add_hop_host(this_hop_n, host, **host_attrs)


class MTRParserInteractive(MTRParser):

    DESCRIPTION = "MTR (interactive)"

    EXAMPLES = [
        "tests/data/traceroute/mtr_interactive_2.txt"
    ]

    @staticmethod
    def _get_hop_n(line: str) -> Tuple[int, str]:

        #  1. 192.168.1.254         0.0%    12    3.3  11.6   2.0  50.7  15.1
        #  2. 10.1.131.181          0.0%    12    9.5  38.3   8.8 112.8  41.9

        first_col = line.strip().split()[0].strip()
        rest_of_the_line = " ".join(line.strip().split()[1:])

        if first_col.endswith("."):
            raw_hop_n = first_col[:-1]
        else:
            raw_hop_n = first_col

        if not raw_hop_n.isdigit():
            raise ParserError(f"the parsed hop is not numeric: {raw_hop_n}")

        return int(raw_hop_n), rest_of_the_line
