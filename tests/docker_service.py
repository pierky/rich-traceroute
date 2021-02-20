from typing import Optional, Dict
import time

import docker
from docker.models.containers import Container

CONTAINER_IMAGE = "rabbitmq:3-management"
CONTAINER_NAME = "rich_traceroute_rabbitmq"

docker_client = docker.from_env()


class DockerService:

    CONTAINER_IMAGE: str

    CHECK_SERVICE_READY_CMD: str

    PORTS: Dict[int, int] = {}

    ENV_VARS: Dict[str, str] = {}

    def __init__(self, container_name: str):
        self.container_name = container_name

        self.container = self.get_existing_container(self.container_name)

    def ensure_is_up(self):
        if not self.container:
            print(f"DOCKER: spinning up new container {self.container_name}...")

            self.container = self.spinup_new_container()

            time.sleep(2)

            print(f"DOCKER: new container {self.container_name} spun up, "
                  "waiting for the service to be ready...")

            self.wait_for_service_to_be_ready()

            print(f"DOCKER: container {self.container_name}, service is ready")
        else:
            print(f"DOCKER: container {self.container_name} already exists, "
                  "checking if it's ready to handle requests...")

            self.wait_for_service_to_be_ready()

        print(f"DOCKER: container {self.container_name} up & running")

    def kill_existing_container(self):
        if not self.container:
            return

        print(f"DOCKER: killing container {self.container_name}")

        self.container.kill()
        self.container = None

        print(f"DOCKER: container {self.container_name} killed")

        time.sleep(2)

    @staticmethod
    def get_existing_container(name: str) -> Optional[Container]:
        containers = docker_client.containers.list()

        for container in containers:
            if container.name == name:
                return container

        return None

    def spinup_new_container(self) -> Container:
        # docker run \
        #     -it \
        #     --rm \
        #     --name rabbitmq \
        #     -p 5672:5672 \
        #     -p 15672:15672 \
        #     rabbitmq:3-management
        container = docker_client.containers.run(
            self.CONTAINER_IMAGE,
            auto_remove=True,
            detach=True,
            ports=self.PORTS,
            environment=self.ENV_VARS,
            name=self.container_name
        )

        print(f"DOCKER: container {self.container_name} created, waiting for it to be up...")

        EXPECTED_STATUS = "created"

        attempts = 0

        while True:
            status = container.status

            if status != EXPECTED_STATUS:
                if attempts > 3:
                    try:
                        container.kill()
                    except:  # noqa: E722
                        pass

                    raise ValueError(
                        f"{self.container_name} container still not running: "
                        f"status is '{status}', expected '{EXPECTED_STATUS}'."
                    )

                attempts += 1

                print("DOCKER: still waiting...")
                time.sleep(1)

            else:
                return container

    def _reset(self):
        raise NotImplementedError()

    def reset(self):
        if not self.container:
            raise ValueError("Container not running")

        self._reset()

    def _wait_for_service_to_be_ready(self):
        attempts = 0

        while True:
            exit_code, _ = self.container.exec_run(self.CHECK_SERVICE_READY_CMD)

            if exit_code != 0:
                if attempts > 3:
                    try:
                        self.kill_existing_container()
                    except:  # noqa: E722
                        pass

                    raise ValueError(
                        f"{self.container_name} still not ready: "
                        f"exit_code of '{self.CHECK_SERVICE_READY_CMD}' is '{exit_code}'."
                    )

                attempts += 1
                time.sleep(2)

            else:
                return

    def wait_for_service_to_be_ready(self):
        if not self.container:
            raise ValueError("Container not running")

        self._wait_for_service_to_be_ready()
