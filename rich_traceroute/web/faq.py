from flask import Blueprint
from flask import render_template

from rich_traceroute.traceroute.parsers import parsers
from rich_traceroute.traceroute.parsers.base import OTHER_UNKNOWN_TRACEROUTE_FORMAT

bp = Blueprint("faq", __name__, url_prefix="")


@bp.route("/faq")
def faq():
    parser_examples = sorted([
        (
            parser_class.__name__,
            parser_class.DESCRIPTION,
            parser_class.get_examples()
        )
        for parser_class in parsers
        if parser_class.DESCRIPTION != OTHER_UNKNOWN_TRACEROUTE_FORMAT
    ], key=lambda tuple: tuple[1])

    # Let's group all the unknown formats into one entry only.
    other_formats_examples = []
    for parser_class in parsers:
        if parser_class.DESCRIPTION == OTHER_UNKNOWN_TRACEROUTE_FORMAT:
            other_formats_examples.extend(parser_class.get_examples())

    parser_examples.append(
        (
            "other_formats",
            OTHER_UNKNOWN_TRACEROUTE_FORMAT,
            other_formats_examples
        )
    )

    return render_template(
        "faq.html",
        parser_examples=parser_examples
    )
