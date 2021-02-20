from .docker_service import DockerService


CONTAINER_IMAGE = "mysql:5"
CONTAINER_NAME = "rich_traceroute_db"

MYSQL_USER = "rich_traceroute_user"
MYSQL_PASS = "rich_traceroute_pass"


class MySQLContainer(DockerService):

    CONTAINER_IMAGE = CONTAINER_IMAGE

    CHECK_SERVICE_READY_CMD = "mysqladmin ping -h localhost"

    PORTS = {
        3306: 3306
    }

    ENV_VARS = {
        "MYSQL_ALLOW_EMPTY_PASSWORD": "yes",
        "MYSQL_USER": MYSQL_USER,
        "MYSQL_PASSWORD": MYSQL_PASS
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.last_schema_name: str = None

    def init_schema(self, schema_name: str):
        if not self.container:
            raise ValueError("Container not running")

        exit_code, output = self.container.exec_run(
            "mysql -e '"
            f"CREATE DATABASE {schema_name}; "
            f"GRANT ALL PRIVILEGES ON {schema_name}.* TO {MYSQL_USER}@localhost IDENTIFIED BY \"{MYSQL_PASS}\";"
            "'"
        )

        if exit_code != 0:
            raise ValueError(
                f"Error while creating new MySQL schema: exit_code {exit_code}\n\n{output}"
            )

        self.last_schema_name = schema_name

    def recreate_last_schema(self):
        self.init_schema(self.last_schema_name)


MYSQL_CONTAINER = MySQLContainer(CONTAINER_NAME)
