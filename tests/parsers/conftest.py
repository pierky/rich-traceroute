import pytest

from rich_traceroute.traceroute.parsers import parse_raw_traceroute


class ParserTestContext:

    def __init__(self):
        self.files = {}

    def parse_test_file(self, path, parser_class):
        if path not in self.files:
            self.files[path] = parser_class
        else:
            if self.files[path] is not parser_class:
                raise ValueError

        raw = open(path).read()

        parser = parser_class(raw)

        parser.parse()

        return parser

    def ensure_best_parser_it_the_one_under_test(self):
        for path, expected_parser_class in self.files.items():
            raw = open(path).read()

            best_parser = parse_raw_traceroute(raw)

            if not isinstance(best_parser, expected_parser_class):
                expected_parser = expected_parser_class(raw)
                expected_parser.parse()

                assert expected_parser.hops == best_parser.hops, \
                    ("According to the prioritized list of parsers, "
                     f"the best parser for {path} is not "
                     f"{expected_parser_class.__name__} but "
                     f"{type(best_parser).__name__}, but the two "
                     "are not generating the same set of hops.")


@pytest.fixture(scope="module")
def parser_ctx():
    global ctx
    ctx = ParserTestContext()

    yield ctx

    ctx.ensure_best_parser_it_the_one_under_test()
