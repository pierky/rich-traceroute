from typing import List
import datetime

from flask import Blueprint
from flask import request
from flask import Response

from rich_traceroute.traceroute import Traceroute
from rich_traceroute.config import load_config

bp = Blueprint("stats", __name__, url_prefix="")

THRESHOLDS = [
    ("not_enriched_perc", 5),
    ("enrichment_not_started_perc", 5),
    ("enrichment_not_completed_perc", 1),
    ("avg_to_start_enrichment", 3),
    ("avg_to_complete_enrichment", 10)
]


class Stats:

    def __init__(self):
        self.total_cnt: int = 0
        self.parsed_cnt: int = 0
        self.not_parsed_cnt: int = 0
        self.enriched_cnt: int = 0
        self.enrichment_not_started_cnt: int = 0
        self.enrichment_not_completed_cnt: int = 0
        self.avg_to_start_enrichment: float = 0
        self.avg_to_complete_enrichment: float = 0

    @property
    def not_enriched_cnt(self):
        return self.parsed_cnt - self.enriched_cnt

    @property
    def not_enriched_perc(self):
        if self.parsed_cnt > 0:
            return self.not_enriched_cnt / self.parsed_cnt
        else:
            return 0

    @property
    def enrichment_not_started_perc(self):
        if self.parsed_cnt > 0:
            return self.enrichment_not_started_cnt / self.parsed_cnt
        else:
            return 0

    @property
    def enrichment_not_completed_perc(self):
        if self.parsed_cnt > 0:
            return self.enrichment_not_completed_cnt / self.parsed_cnt
        else:
            return 0

    def as_dict(self):
        return {
            k: getattr(self, k)
            for k in dir(self)
            if k[:1] != '_'
        }


@bp.route("/stats", methods=["GET"])
def stats():
    token = request.args.get("token", None)

    if not token:
        return "Token not provided"

    lookback_minutes = int(request.args.get("lookback", 60))

    cfg = load_config()

    if cfg["web"].get("stats_token", "") != token:
        return "Token not valid"

    LAST_PERIOD = datetime.timedelta(minutes=lookback_minutes)

    oldest_limit = datetime.datetime.utcnow() - LAST_PERIOD

    traceroutes = Traceroute.select().where(
        Traceroute.created > oldest_limit
    )

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

    stats.avg_to_start_enrichment = 0
    if len(time_to_start_enrichment):
        stats.avg_to_start_enrichment = sum(time_to_start_enrichment) / len(time_to_start_enrichment)

    stats.avg_to_complete_enrichment = 0
    if len(time_to_complete_enrichment):
        stats.avg_to_complete_enrichment = sum(time_to_complete_enrichment) / len(time_to_complete_enrichment)

    res = """
Traceroutes:
- total:         {total_cnt}
- parsed:        {parsed_cnt}
- not parsed:    {not_parsed_cnt}
- enriched:      {enriched_cnt}
- not enriched:  {not_enriched_cnt} ({not_enriched_perc} %)
- not started:   {enrichment_not_started_cnt} ({enrichment_not_started_perc} %)
- not completed: {enrichment_not_completed_cnt} ({enrichment_not_completed_perc} %)
- avg time:
  - to start enrichment:    {avg_to_start_enrichment}
  - to complete enrichment: {avg_to_complete_enrichment}
""".format(**stats.as_dict())

    all_good = True

    for attr, default_value in THRESHOLDS:
        threshold = int(request.args.get(f"threshold_{attr}", default_value))
        value = getattr(stats, attr)

        if value > threshold:
            res += f"ERROR: the value of {attr} ({value}) is above the threshold ({threshold})\n"
            all_good = False

    if all_good:
        res += "ALL GOOD!\n"

    return Response(res, mimetype="text/plain")
