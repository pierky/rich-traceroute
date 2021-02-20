from typing import Dict, List, NamedTuple, Optional
from abc import ABC, abstractmethod
import re


from ...errors import ParserError


HOSTNAME_ALLOWED_LABELS = re.compile(
    r'^[_a-z0-9]([_a-z0-9-]{0,61}[_a-z0-9])?$',
    re.IGNORECASE
)


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
        ...

    @property
    @classmethod
    @abstractmethod
    def EXAMPLES(cls) -> List[str]:
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

    @abstractmethod
    def _parse(self):
        ...

    def parse(self):
        self._parse()

        if not self.hops:
            raise ParserError("No hops found")
