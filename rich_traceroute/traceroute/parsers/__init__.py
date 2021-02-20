from typing import Optional, Type
import logging

from .base import BaseParser
from .mtr_json import MTRJSONParser
from .mtr import MTRParser
from .junos import JunosParser
from .bsd import BSDParser
from .iosxr import IOSXRParser
from .linux import LinuxParser
from .win_tracert import WindowsTracertParser
from ...errors import ParserError

LOGGER = logging.getLogger(__name__)

parsers = [
    MTRJSONParser,
    MTRParser,
    JunosParser,
    LinuxParser,
    IOSXRParser,
    BSDParser,
    WindowsTracertParser
]


def parse_raw_traceroute(raw: str) -> Optional[Type[BaseParser]]:
    # List of all the parsers that are able to process this
    # traceroute.
    possible_parsers = []

    for parser_class in parsers:
        parser = parser_class(raw)

        try:
            parser.parse()
        except ParserError:
            continue
        except:  # noqa: E722
            LOGGER.exception(
                f"Parser error: {parser_class.__name__}\n\n{raw}"
            )

        possible_parsers.append(parser)

    if not possible_parsers:
        return None

    def get_number_of_hosts(p: Type[BaseParser]) -> int:
        res = 0

        for hop in p.hops:
            res += len(p.hops[hop])

        return res

    # Return the "best" parser for the input provided
    # in 'raw', where the definition of "best" is based
    # on the number of hops that every parser was able
    # to extract. The more hops and hosts a parser was
    # able to parse, the better.
    return sorted(
        possible_parsers,
        key=lambda p: -get_number_of_hosts(p)
    )[0]
