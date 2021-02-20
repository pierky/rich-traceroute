from typing import Tuple

from .mtr import MTRParser
from ...errors import ParserError


class JunosParser(MTRParser):

    DESCRIPTION = "Junos"

    EXAMPLES = [
        "tests/data/traceroute/junos_1.txt"
    ]

    @staticmethod
    def _get_hop_n(line: str) -> Tuple[int, str]:
        first_part = line.split()[0]

        if not first_part.endswith("."):
            raise ParserError("a dot was expected at the end of "
                              f"the first part ({first_part})")

        raw_hop_n = first_part.replace(".", "")

        if not raw_hop_n.isdigit():
            raise ParserError(f"the parsed hop is not numeric: {raw_hop_n}")

        return int(raw_hop_n), " ".join(line.split()[1:])
