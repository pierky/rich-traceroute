#!/usr/bin/env python
from typing import List
from dataclasses import dataclass, asdict
import datetime
import sys
import argparse

from rich_traceroute.traceroute import Traceroute
from rich_traceroute.db import (
    connect_to_the_db,
    disconnect_from_the_db
)
from rich_traceroute.config import load_config

parser = argparse.ArgumentParser()
parser.add_argument(
    "-o", "--output",
    help="Path of the output file. " +
         "Default: stdout",
)
parser.add_argument(
    "-l", "--lookback",
    type=int,
    help="How many hours to look back. "
         "Default: 1",
    default=1
)

args = parser.parse_args()


LAST_PERIOD = datetime.timedelta(hours=args.lookback)

load_config()
connect_to_the_db(max_attempts=3)

oldest_limit = datetime.datetime.utcnow() - LAST_PERIOD
traceroutes = Traceroute.select().where(
    Traceroute.created > oldest_limit
)


@dataclass
class Stats:
    total_cnt: int = 0
    parsed_cnt: int = 0
    not_parsed_cnt: int = 0
    enriched_cnt: int = 0
    enrichment_not_started_cnt: int = 0
    enrichment_not_completed_cnt: int = 0
    avg_to_start_enrichment: float = 0
    avg_to_complete_enrichment: float = 0


time_to_complete_enrichment: List[int] = []
time_to_start_enrichment: List[int] = []

stats = Stats()

for t in traceroutes:
    stats.total_cnt += 1

    if not t.parsed:
        stats.not_parsed_cnt += 1
        continue

    stats.parsed_cnt += 1

    if not t.enrichment_started:
        stats.enrichment_not_started_cnt += 1
        continue

    time_to_start_enrichment.append(
        (t.enrichment_started - t.created).total_seconds()
    )

    if t.enrichment_started and not t.enrichment_completed:
        stats.enrichment_not_completed_cnt += 1
        continue

    if t.enriched:
        stats.enriched_cnt += 1

        time_to_complete_enrichment.append(
            (t.enrichment_completed - t.enrichment_started).total_seconds()
        )


if not args.output:
    output_file = sys.stdout
else:
    output_file = open(args.output, "w")

stats.avg_to_start_enrichment = None
if len(time_to_start_enrichment):
    stats.avg_to_start_enrichment = sum(time_to_start_enrichment) / len(time_to_start_enrichment)

stats.avg_to_complete_enrichment = None
if len(time_to_complete_enrichment):
    stats.avg_to_complete_enrichment = sum(time_to_complete_enrichment) / len(time_to_complete_enrichment)

output_file.write("""
Traceroutes:
- total:         {total_cnt}
- parsed:        {parsed_cnt}
- not parser:    {not_parsed_cnt}
- enriched:      {enriched_cnt}
- not started:   {enrichment_not_started_cnt}
- not completed: {enrichment_not_completed_cnt}
- avg time:
  - to start enrichment:    {avg_to_start_enrichment}
  - to complete enrichment: {avg_to_complete_enrichment}
""".format(**asdict(stats)))

disconnect_from_the_db()
