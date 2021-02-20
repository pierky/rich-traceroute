from flask import Blueprint
from flask import render_template

from rich_traceroute.traceroute.parsers import parsers

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
    ], key=lambda tuple: tuple[1])
    return render_template(
        "faq.html",
        parser_examples=parser_examples
    )
