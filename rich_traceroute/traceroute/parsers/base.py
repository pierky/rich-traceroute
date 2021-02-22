from typing import Dict, List, NamedTuple, Optional
from abc import ABC, abstractmethod
import re


from ...errors import ParserError


HOSTNAME_ALLOWED_LABELS = re.compile(
    r'^[_a-z0-9]([_a-z0-9-]{0,61}[_a-z0-9])?$',
    re.IGNORECASE
)

# This is the string to be used as the DESCRIPTION of the
# parsers for which the origin of the format is unknown.
# It is used by the WEB FAQ page to group all those parsers
# into one example only.
OTHER_UNKNOWN_TRACEROUTE_FORMAT = "Other formats"


class HopHost(NamedTuple):

    host: str
    loss: Optional[float]
    avg_rtt: Optional[float]
    min_rtt: Optional[float]
    max_rtt: Optional[float]


class BaseParser(ABC):

    @property
    @classmethod
    @abstractmethod
    def DESCRIPTION(cls) -> str:
        """Short description of the format that this parser is able to understand."""
        ...

    @property
    @classmethod
    @abstractmethod
    def EXAMPLES(cls) -> List[str]:
        """List of files containing example texts that this parser can understand."""
        ...

    @classmethod
    def get_examples(cls) -> List[str]:
        res = []

        for file in cls.EXAMPLES:  # type: ignore
            res.append(
                open(file, "r").read()
            )

        return res

    def __init__(self, raw_data: str):
        self.raw_data = raw_data

        # This must be set by the parser on exist.
        # The number of each hop must be the key,
        # and the value must be a list of hosts
        # for which replies were received for that hop.
        # If no replies were found for a specific hop,
        # the list must be empty.
        self.hops: Dict[int, List[HopHost]] = {}

    @staticmethod
    def looks_like_a_hostname(hostname) -> bool:
        if hostname.lower() in ("ms", "msec"):
            return False

        if hostname.endswith('.'):
            hostname = hostname[:-1]

        if len(hostname) < 1 or len(hostname) > 253:
            return False

        # Let's assume that strings shorter than 4 chars are
        # not representing a hostname.
        if len(hostname) < 4:
            return False

        return all(
            HOSTNAME_ALLOWED_LABELS.match(label)
            for label in hostname.split('.')
        )

    @staticmethod
    def extract_rtt_from_str(s: str) -> float:
        if s.endswith("ms"):
            s = s[:-2].strip()
        elif s.endswith("msec"):
            s = s[:-4].strip()

        return float(s)

    @abstractmethod
    def _parse(self):
        ...

    def parse(self):
        self._parse()

        if not self.hops:
            raise ParserError("No hops found")

        expected_hop = 1
        for hop_n in self.hops:
            if hop_n != expected_hop:
                raise ParserError(
                    f"Hop n. {expected_hop} was expected, "
                    f"but {hop_n} was found."
                )

            expected_hop += 1
