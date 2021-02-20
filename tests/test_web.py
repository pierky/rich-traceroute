import time
import pytest

from rich_traceroute.traceroute import Traceroute
from rich_traceroute.web import create_app


@pytest.fixture
def app(mocker):

    def _void(*args):
        return

    mocker.patch("rich_traceroute.web.setup_environment", _void)

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    flask_app.config["DEBUG"] = True

    with flask_app.app_context():
        yield flask_app


@pytest.fixture(autouse=True)
def client(app):
    return app.test_client()


@pytest.fixture()
def good_recaptcha(mocker):

    def fake_check_user_response(*args, **kwargs):
        return True

    mocker.patch("rich_traceroute.web.traceroute.ReCaptcha.check_user_response", fake_check_user_response)


def test_web_home(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"<title>rich-traceroute.io</title>" in res.data
    assert (b'<h1 class="mt-2"><img style="padding-right: 10px" '
            b'src="/static/favicon/favicon-32x32.png">rich-traceroute.io</h1>') in res.data

    # Be sure that when the home is loaded, we're using ReCaptcha 3.
    assert b"ReCaptcha3" in res.data


def test_web_create_traceroute_bad_recaptcha(client):
    raw = open("tests/data/traceroute/mtr_json_1.json").read()
    res = client.post(
        "/new_traceroute",
        data=dict(
            raw=raw
        ),
        follow_redirects=True
    )

    assert res.status_code == 200

    # Be sure that when the first ReCaptcha3 attempt fails, we switch to
    # ReCaptcha2.
    assert b"ReCaptcha2" in res.data


def test_web_create_traceroute_recaptcha_ok(client, good_recaptcha, db, rabbitmq):
    raw = open("tests/data/traceroute/mtr_json_1.json").read()
    res = client.post(
        "/new_traceroute",
        data=dict(
            raw=raw
        ),
        follow_redirects=True
    )

    assert res.status_code == 200

    # Wait a bit to let enrichers complete their work.
    time.sleep(2)

    t = Traceroute.select()[0]

    assert t.parsed is True
    assert t.enriched is True
    assert t.last_seen is not None
    last_seen_1 = t.last_seen

    assert res.status_code == 200
    assert f"<h4>Traceroute ID {t.id}".encode() in res.data, res.data

    # To be sure that we're putting the meta to avoid traceroute pages indexing.
    assert b'<meta name="robots" content="noindex">' in res.data

    # The content of res.data represents the web page that was generated
    # as soon as the traceroute was created, so it contains all the
    # elements of a work in progress traceroute. Even though at this point
    # the actual traceroute should be already fully enriched, the information
    # do not show up in the page yet; in the real live experience the browser
    # receives the enriched data via SocketIO and updates the content using
    # JavaScript.

    # Checking that enriched information don't show up in the web page.
    assert b"15169" not in res.data
    assert b"12874" not in res.data

    # Now, let's request the traceroute web page again. At this point, fresh
    # content is generated and somewhere, in the HTML code, there should be
    # the JSON that contains all the information about the newly created traceroute.
    # Also, the traceroute should NOT be marked with the graphical component that
    # identifies it as WIP.

    res = client.get(f"/t/{t.id}")
    assert res.status_code == 200
    assert t.to_json().encode() in res.data

    assert b'<div class="spinner-border spinner-border-sm" role="status" id="tr_status_wip">' not in res.data

    # Check that the last_seen attribute of the traceroute is more recent than
    # how it was when the traceroute was created.
    t = Traceroute.select()[0]

    last_seen_2 = t.last_seen

    assert last_seen_2 > last_seen_1


def test_web_unexisting_traceroute(client, good_recaptcha, db):
    res = client.get(
        "/t/123456",
        follow_redirects=True
    )

    assert res.status_code == 200

    assert b'<h4 class="alert-heading">Traceroute not found.</h4>' in res.data
