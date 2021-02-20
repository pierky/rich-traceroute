import json

from .base import BaseParser, HopHost
from ...errors import ParserError


class MTRJSONParser(BaseParser):

    DESCRIPTION = "MTR JSON"

    EXAMPLES = [
        "tests/data/traceroute/mtr_json_1.json",
        "tests/data/traceroute/mtr_json_3.json",
    ]

    def _parse(self):
        try:
            data = json.loads(self.raw_data)
        except:  # noqa: E722
            raise ParserError("Not a valid JSON") from None

        if "report" in data:
            if "hubs" not in data["report"]:
                raise ParserError("report.hubs was expected, "
                                  "but was not found")

            hops = data["report"]["hubs"]

            name_of_hop_n_key = "count"
            name_of_host_key = "host"
            name_of_loss_key = "Loss%"
            name_of_rtt_avg_key = "Avg"
            name_of_rtt_min_key = "Best"
            name_of_rtt_max_key = "Wrst"

        elif "hops" in data:
            hops = data["hops"]

            name_of_hop_n_key = "hop"
            name_of_host_key = "ipaddr"
            name_of_loss_key = "losspercent"
            name_of_rtt_avg_key = "avg"
            name_of_rtt_min_key = "best"
            name_of_rtt_max_key = "worst"

        else:
            raise ParserError("Couldn't find hops/hubs")

        for hop in hops:
            try:
                hop_n = int(hop[name_of_hop_n_key])

                if hop_n not in self.hops:
                    self.hops[hop_n] = []

                host = hop[name_of_host_key]
                if host != "???":
                    self.hops[hop_n].append(
                        HopHost(
                            host=host,
                            loss=float(hop[name_of_loss_key]),
                            avg_rtt=float(hop[name_of_rtt_avg_key]),
                            min_rtt=float(hop[name_of_rtt_min_key]),
                            max_rtt=float(hop[name_of_rtt_max_key])
                        )
                    )
            except Exception as e:
                raise ParserError(
                    "Something went wrong while parsing "
                    f"the JSON: {e}"
                ) from e
