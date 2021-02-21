from typing import (
    Union,
    Optional,
    Dict,
    List,
    Tuple,
    Mapping
)
import ipaddress

from .base import BaseParser, HopHost
from ...errors import ParserError

IPAddress = Union[
    ipaddress.IPv4Address,
    ipaddress.IPv6Address
]


class LineByLineParser(BaseParser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dictionary whose keys are the n. of the hops
        # for this traceroute, and values are either
        # None (meaning that no replies were observed
        # for that hop) or a dict of hosts and their
        # RTTs.
        self.internal_repr: Dict[
            int,
            Union[
                Mapping[str, List[float]],
                None
            ]
        ] = {}

    def _add_host_info(
        self,
        hop_n: int,
        host_rtts: Optional[Tuple[Union[IPAddress, str], List[float]]]
    ) -> None:
        """Incrementally add information about a hop to the internal structure.

        This function adds information about a hop to the internal
        structure that is eventually used to generate the self.hops
        output of the parser.

        Args:
            hop_n (int): the n. of the hop for which information
                are going to be added.
            host_rtts (tuple): host and list of RTTs representing
                the information to be added.

        If host_rtts is None, it means that no replies were
        received for this hop. Otherwise, it must be a tuple whose
        first item is a host (either an ipaddress.IPvXAddress or
        a string) and the second item is a list of RTT values to
        be added.

        The function can be called multiple times for the same hop
        and host, in which case the RTT values are just appended to
        the list of RTT values for that host.
        """

        if hop_n not in self.internal_repr:
            if not host_rtts:
                self.internal_repr[hop_n] = None
                return
            else:
                self.internal_repr[hop_n] = {}

        if not host_rtts:
            raise ParserError(
                f"For hop n. {hop_n} a total absence of "
                "replies is observed, but a record already "
                "exists in hop_hosts. Why?"
            )

        host_str: str = str(host_rtts[0])
        rtts: List[float] = host_rtts[1]

        if isinstance(self.internal_repr[hop_n], dict):
            if host_str not in self.internal_repr[hop_n]:  # type: ignore
                self.internal_repr[hop_n][host_str] = []  # type: ignore

            self.internal_repr[hop_n][host_str].extend(rtts)  # type: ignore
        else:
            raise ParserError(
                f"For hop n. {hop_n} host {host_str} was "
                "found but the hop_hosts record is None. "
                "Why?"
            )

    def _build_internal_repr(self):
        raise NotImplementedError()

    def _parse(self):
        try:
            self._build_internal_repr()
        except ParserError:
            raise
        except Exception as e:
            raise ParserError(
                "Something went wrong while parsing "
                f"the traceroute: {e}"
            ) from e

        if not self.internal_repr:
            raise ParserError(
                "No hops found"
            )

        last_hop_n: int = 0

        for hop_n, hosts_rtts in self.internal_repr.items():
            if hop_n != last_hop_n + 1:
                raise ParserError(
                    "Error while validating the internal_repr: "
                    f"hop n. {hop_n} found, but the previous one "
                    f"was {last_hop_n}."
                )

            if hop_n not in self.hops:
                self.hops[hop_n] = []

            if hosts_rtts:
                for host, rtts in hosts_rtts.items():
                    if host and not rtts:
                        raise ParserError(
                            "Error while validating the internal_repr: "
                            f"host {host} at hop n. {hop_n} has no RTTs."
                        )

                    self.hops[hop_n].append(
                        HopHost(
                            host=host,
                            loss=None,
                            avg_rtt=round(sum(rtts) / len(rtts), 3) if rtts else None,
                            min_rtt=min(rtts) if rtts else None,
                            max_rtt=max(rtts) if rtts else None
                        )
                    )

            last_hop_n += 1
