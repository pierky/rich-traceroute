from .docker_service import DockerService


CONTAINER_IMAGE = "rabbitmq:3-management"
CONTAINER_NAME = "rich_traceroute_rabbitmq"


class RabbitMQContainer(DockerService):

    CONTAINER_IMAGE = CONTAINER_IMAGE

    CHECK_SERVICE_READY_CMD = "rabbitmqctl status"

    PORTS = {
        5672: 5672,
        15672: 15672
    }

    def _reset(self):
        exit_code, _ = self.container.exec_run(
            "bash -c '"
            "rabbitmqctl stop_app && "
            "rabbitmqctl reset && "
            "rabbitmqctl start_app"
            "'"
        )

        if exit_code != 0:
            raise ValueError(
                f"Error while resetting RabbitMQ: exit_code {exit_code}"
            )


RABBIT_MQ_CONTAINER = RabbitMQContainer(CONTAINER_NAME)
