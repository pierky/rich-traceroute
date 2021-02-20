import os
import logging
import time

from peewee import (
    DatabaseProxy,
    SqliteDatabase,
    MySQLDatabase,
    Model
)
from playhouse.shortcuts import ReconnectMixin


from ..config import get_db_config

LOGGER = logging.getLogger(__name__)

db = DatabaseProxy()


class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):

    def connect(self, *args, **kwargs):
        delay = 1

        while True:
            try:
                super().connect(*args, **kwargs)

                # Recreate the tables if needed, but do not
                # fail if something goes wrong here.
                # Recreating tables is useful only for the tests,
                # when the entire container where MySQL runs is
                # destroyed and recreated from scratch (then, a new
                # schema is created, and it doesn't contain any table).
                # In prod, the tables are created when the DB is
                # initialised, and they are expected to remain in place
                # even if the connection to the DB is lost.
                try:
                    super().create_tables(BaseModel.__subclasses__())
                except:  # noqa: E722
                    pass

                return
            except Exception as exc:
                exc_class = type(exc)

                if exc_class not in self._reconnect_errors:
                    raise exc

                exc_repr = str(exc).lower()
                for err_fragment in self._reconnect_errors[exc_class]:
                    if err_fragment in exc_repr:
                        break
                else:
                    raise exc

                delay = delay * 2

                if delay > 60:
                    delay = 60

                LOGGER.warning(
                    f"Connection to the database failed: {exc}. "
                    f"Attempting a new connection in {delay} seconds..."
                )

                time.sleep(delay)


class BaseModel(Model):

    class Meta:
        database = db


def connect_via_sqlite(path):
    db.initialize(
        SqliteDatabase(
            os.path.expanduser(path),
            pragmas={"foreign_keys": 1}
        )
    )


def connect_via_mysql(schema, host, port, user, passwd):
    LOGGER.info(
        f"Connecting to DB {schema} on {host}:{port}..."
    )

    db.initialize(
        ReconnectMySQLDatabase(
            schema,
            host=host,
            port=port,
            user=user,
            passwd=passwd
        )
    )


def _get_db_path(db_config):
    return db_config["path"]


def _get_db_init_args(db_config):
    return (
        db_config["schema"],
        db_config["host"],
        db_config["port"],
        db_config["user"],
        db_config["passwd"]
    )


def _get_db_type(db_config):
    return db_config["type"]


def connect_to_the_db():
    db_config = get_db_config()

    if _get_db_type(db_config) == "sqlite":
        connect_via_sqlite(_get_db_path(db_config))
    else:
        connect_via_mysql(*_get_db_init_args(db_config))

    db.create_tables(BaseModel.__subclasses__())


def disconnect_from_the_db():
    try:
        if not db.is_closed():
            db.close()
    except Exception:
        pass
