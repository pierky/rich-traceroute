from flask import Blueprint
from flask import render_template
from flask import request

from .recaptcha import ReCaptcha

bp = Blueprint("home", __name__, url_prefix="")


@bp.route("/")
def index():
    err_code = int(request.args.get("err_code", 0))

    if ReCaptcha.is_used():
        return render_template(
            "index.html",
            recaptcha=ReCaptcha(3),
            err_code=err_code
        )
    else:
        return render_template(
            "index.html",
            err_code=err_code
        )
