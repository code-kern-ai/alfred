import json

from util.constants import (
    DOCKER_COMPOSE,
    DOCKER_COMPOSE_TEMPLATE,
    SERVICE_VERSIONS,
    SETTINGS,
)
from util.docker_helper import get_credential_ip, get_host_ip


def process_docker_compose_template():
    credential_ip = get_credential_ip()
    host_ip = get_host_ip()

    cred_endpoint = f"http://{credential_ip}:7053"
    minio_endpoint = f"http://{host_ip}:7053"

    with open(DOCKER_COMPOSE_TEMPLATE, "r") as f:
        template = f.read()

    with open(SERVICE_VERSIONS, "r") as f:
        versions = json.load(f)

    with open(SETTINGS, "r") as f:
        settings = json.load(f)

    docker_compose = template.format(
        **versions,
        **settings,
        **{
            "CRED_ENDPOINT": cred_endpoint,
            "MINIO_ENDPOINT": minio_endpoint,
        },
    )

    with open(DOCKER_COMPOSE, "w") as f:
        f.write(docker_compose)

    return minio_endpoint
