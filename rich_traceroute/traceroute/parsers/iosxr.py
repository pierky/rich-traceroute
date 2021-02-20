import re

from .bsd import BSDParser


class IOSXRParser(BSDParser):

    DESCRIPTION = "IOS-XR"

    EXAMPLES = [
        "tests/data/traceroute/iosxr_2.txt"
    ]

    def _build_internal_repr(self):
        # This is to remove "extra string" like the
        # MPLS labels before processing the traceroute
        # like a regulard BSD-style one.
        #
        # Ex.: [MPLS: Label 1111 Exp 0]

        self.raw_data = re.sub(
            r"\[MPLS:.+\]",
            "",
            self.raw_data
        )

        super()._build_internal_repr()
