import datetime

from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify
from peewee import DoesNotExist

from rich_traceroute.traceroute import (
    Traceroute,
    create_traceroute
)
from .recaptcha import ReCaptcha


bp = Blueprint("traceroute", __name__, url_prefix="")


@bp.route("/status", methods=["GET"])
def status():
    traceroute_id = request.args.get("id")
    try:
        traceroute = Traceroute.get(Traceroute.id == traceroute_id)
    except DoesNotExist:
        return jsonify({"status": "not found"})

    return jsonify({"status": traceroute.status})


@bp.route("/t/<traceroute_id>", methods=["GET"])
def t(traceroute_id):
    try:
        traceroute = Traceroute.get(Traceroute.id == traceroute_id)
    except DoesNotExist:
        return render_template(
            "traceroute.html",
            err_code=1
        )

    traceroute.last_seen = datetime.datetime.utcnow()
    traceroute.save()

    return render_template(
        "traceroute.html",
        t=traceroute
    )


@bp.route("/new_traceroute", methods=["POST"])
def new():
    raw = request.form["raw"]

    if not raw.split():
        return redirect(
            url_for(
                "home.index",
                err_code=3
            )
        )

    if ReCaptcha.is_used():
        user_recaptcha_data = request.form.get("g-recaptcha-response")
        recaptcha_ver = int(request.form.get("recaptcha-ver", 3))

        recaptcha = ReCaptcha(recaptcha_ver)

        if not recaptcha.check_user_response(user_recaptcha_data):
            if recaptcha_ver == 3:
                return render_template(
                    "index.html",
                    recaptcha=ReCaptcha(2),
                    raw=raw
                )
            else:
                return render_template(
                    "index.html",
                    err_code=1,
                    raw=raw
                )

    traceroute = create_traceroute(raw)

    if not traceroute.parsed:
        return render_template(
            "index.html",
            recaptcha=ReCaptcha(3) if ReCaptcha.is_used() else None,
            err_code=2,
            raw=raw
        )

    return redirect(
        url_for("traceroute.t", traceroute_id=traceroute.id)
    )
