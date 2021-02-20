from flask import Blueprint
from flask import render_template

bp = Blueprint("static_content", __name__, url_prefix="")


@bp.route("/contacts")
def contacts():
    return render_template("contacts.html")


@bp.route("/cookies")
def cookies():
    return render_template("cookies.html")


@bp.route("/privacy")
def privacy():
    return render_template("privacy.html")


@bp.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")
