from enum import Enum
import datetime
import os

import pika
import yaml

from .errors import ConfigError

CONFIG = None

IP_INFO_EXPIRY = datetime.timedelta(days=7)
TRACEROUTE_EXPIRY = datetime.timedelta(days=7)

DNS_QUERY_TIMEOUT = 5
DNS_CACHE_TTL = 30 * 60  # seconds

MAX_ENRICHMENT_TIME = datetime.timedelta(minutes=2)

SOCKET_IO_DATA_EVENT = "traceroute_host_enriched"
SOCKET_IO_ERROR_EVENT = "traceroute_host_enrichment_error"
SOCKET_IO_ENRICHMENT_COMPLETED_EVENT = "traceroute_enrichment_completed"

IXP_NETWORKS_UPDATE_INTERVAL = 3 * 60 * 60  # 3 hours

HOUSEKEEPER_INTERVAL = 6 * 60 * 60  # 6 hours


class ConfigMode(Enum):

    WEB = "web"
    WORKER = "worker"


def _get_config_file_path():
    path = os.environ.get("RICH_TRACEROUTE_CONFIG", None)
    if path:
        return path

    for well_known_path in (
        "rich_traceroute.yml",
        "~/.rich_traceroute.yml",
        "/usr/local/etc/rich_traceroute/config.yml",
        "/usr/local/etc/rich_traceroute.yml",
        "/etc/rich_traceroute/config.yml",
        "/etc/rich_traceroute.yml",
        "private/config.yml",
    ):
        path = os.path.expanduser(well_known_path)
        if os.path.exists(path):
            print(f"Reading configuration from {path}")
            return path
    else:
        raise ConfigError(
            "Configuration file not found."
        )


def load_config(config_file_path: str = None):
    global CONFIG

    if CONFIG:
        return CONFIG

    config_file_path = config_file_path or _get_config_file_path()

    with open(config_file_path, "r") as f:
        try:
            CONFIG = yaml.safe_load(f)
        except Exception as e:
            raise ConfigError(
                "Error while loading the configuration "
                f"from {config_file_path}: {e}"
            ) from e

    # ALLOWED_MODES = ("full", "enrichers-only")

    # if CONFIG.get("mode", "") not in ALLOWED_MODES:
    #     raise ConfigError(
    #         "Unknown mode: must be one of {}".format(
    #             ", ".join(ALLOWED_MODES)
    #         )
    #     )

    # DB
    # ----------------------

    if "db" not in CONFIG:
        raise ConfigError("Database configuration is missing: 'db' not found")

    if "type" not in CONFIG["db"]:
        raise ConfigError("Database configuration error: 'db.type' not found")

    ALLOWED_DB_TYPES = ("sqlite", "mysql")

    if CONFIG["db"]["type"] not in ALLOWED_DB_TYPES:
        raise ConfigError(
            "Database configuration error: "
            "'db.type' must be one of {}".format(
                ", ".join(ALLOWED_DB_TYPES)
            )
        )

    if CONFIG["db"]["type"] == "mysql":
        MANDATORY_DB_PARAMS = ["schema", "host", "port", "user", "passwd"]
    elif CONFIG["db"]["type"] == "sqlite":
        MANDATORY_DB_PARAMS = ["path"]

    for param in MANDATORY_DB_PARAMS:
        if not CONFIG["db"].get(param, None):
            raise ConfigError(
                "Database configuration error: "
                f"'db.{param}' is missing"
            )

    # RabbitMQ
    # ----------------------

    if "rabbitmq" not in CONFIG:
        raise ConfigError("RabbitMQ configuration is missing: 'rabbitmq' not found")

    params = CONFIG["rabbitmq"]

    if "url" not in params:
        for param in ("protocol", "username", "password", "host", "port"):
            if not params.get(param, ""):
                raise ConfigError(
                    f"RabbitMQ config error, missing parameter: '{param}'"
                )

        if not isinstance(params["port"], int):
            if not params["port"].isdigit():
                raise ConfigError(
                    "RabbitMQ configuration error, 'port' must be an integer"
                )

            params["port"] = int(params["port"])

    # Workers
    # ----------------------

    if "workers" not in CONFIG:
        raise ConfigError("Workers configuration is missing: 'workers' not found")

    for param in ["consumers", "enrichers"]:
        if not CONFIG["workers"].get(param, None):
            raise ConfigError("Workers configuration is missing: "
                              f"'workers.{param}' not found")

        val = CONFIG["workers"][param]
        if not isinstance(val, int):
            if not val.isdigit():
                raise ConfigError("Workers configuration error: "
                                  f"'workers.{param}' must be an integer")

            val = int(val)

            if val < 0:
                raise ConfigError("Workers configuration error: "
                                  f"'workers.{param}' must be >= 0")

            CONFIG["workers"][param] = val

    # Web
    # ----------------------

    if "web" not in CONFIG:
        raise ConfigError("Web configuration is missing: 'web' not found")

    if "flask" not in CONFIG["web"]:
        raise ConfigError("Flask configuration is missing: 'web.flask' not found")

    if not CONFIG["web"]["flask"].get("secret_key", "").strip():
        raise ConfigError("Flask secret key is missing: 'web.flask.secret_key' not found")

    if "recaptcha" in CONFIG["web"]:
        for v in ("v2", "v3"):
            if not CONFIG["web"]["recaptcha"].get(v, None):
                raise ConfigError(
                    f"Recaptca configuration error: 'web.recaptcha.{v}' is missing"
                )

            for key in ("pub_key", "pvt_key"):
                if not CONFIG["web"]["recaptcha"][v].get(key, None):
                    raise ConfigError(
                        f"Recaptca configuration error: 'web.recaptcha.{v}.{key}' is missing"
                    )

    return CONFIG


def get_pika_url_parameters():
    return pika.URLParameters(get_rabbitmq_url())


def get_rabbitmq_url():
    load_config()

    params = CONFIG["rabbitmq"]

    if "url" in params:
        return params["url"]

    return "{protocol}://{username}:{password}@{host}:{port}/{vhost}".format(
        **params
    )


def get_flask_secret_key():
    load_config()
    return CONFIG["web"]["flask"]["secret_key"]


def get_markus_options():
    load_config()
    return CONFIG.get("markus_params", [])


def get_logging_config():
    load_config()
    return CONFIG.get("logging", {})


def get_recaptcha_settings():
    load_config()
    return CONFIG["web"].get("recaptcha", None)


def get_db_config():
    load_config()
    return CONFIG["db"]
