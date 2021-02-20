#!/usr/bin/env python
import sys
import pprint
import traceback


from rich_traceroute.traceroute.parsers import parsers

print("Paste the traceroute and press CTRL-D")
raw_data = sys.stdin.read()

if len(sys.argv) > 1:
    parser_class_name = sys.argv[1]
    print(f"Parsing the traceroute using the selected parser {parser_class_name}...")
else:
    parser_class_name = None
    print("Parsing the traceroute using all the available parsers...")

for parser_class in parsers:
    if not parser_class_name or parser_class.__name__ == parser_class_name:
        print(f"{parser_class.__name__}")
        print("=" * len(f"{parser_class.__name__}"))

        parser = parser_class(raw_data)

        try:
            parser.parse()
            print("It worked!")

            pprint.pprint(parser.hops)
        except Exception:
            traceback.print_exc()

        print("\n\n")
