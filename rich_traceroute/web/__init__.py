import logging

from rich_traceroute.config import (
    get_flask_secret_key,
    SOCKET_IO_DATA_EVENT,
    SOCKET_IO_ERROR_EVENT,
    SOCKET_IO_ENRICHMENT_COMPLETED_EVENT,
)
from rich_traceroute.main import setup_environment
from rich_traceroute.config import load_config, get_rabbitmq_url, ConfigMode

from .home import bp as bp_home
from .traceroute import bp as bp_traceroute
from .static_content import bp as bp_static_content
from .faq import bp as bp_faq

from flask import Flask
from flask_socketio import SocketIO


LOGGER = logging.getLogger(__name__)


def create_app(*args):
    setup_environment(ConfigMode.WEB)

    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=get_flask_secret_key(),
    )

    app.register_blueprint(bp_home)
    app.register_blueprint(bp_traceroute)
    app.register_blueprint(bp_static_content)
    app.register_blueprint(bp_faq)

    socketio = SocketIO()
    socketio.init_app(
        app,
        message_queue=get_rabbitmq_url(),
        cors_allowed_origins="*"
    )

    app.context_processor(inject_global_variables)

    return app


def inject_global_variables():
    return dict(
        SOCKET_IO_DATA_EVENT=SOCKET_IO_DATA_EVENT,
        SOCKET_IO_ERROR_EVENT=SOCKET_IO_ERROR_EVENT,
        SOCKET_IO_ENRICHMENT_COMPLETED_EVENT=SOCKET_IO_ENRICHMENT_COMPLETED_EVENT,
        CONFIG=load_config()
    )
