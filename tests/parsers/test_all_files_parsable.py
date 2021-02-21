from os.path import isfile
import glob

from rich_traceroute.traceroute.parsers import parse_raw_traceroute


def test_all_parser_test_files_parsable():
    # Dirt way to verify that all the test files present in
    # the directory are actually parsable.
    test_files = glob.glob("tests/data/traceroute/*")

    for f in test_files:
        if not isfile(f):
            continue

        parse_raw_traceroute(open(f, "r").read())
