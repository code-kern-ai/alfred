import json
import os

from util.constants import (
    DOCKER_COMPOSE,
    DOCKER_COMPOSE_TEMPLATE,
    SERVICE_VERSIONS,
    SETTINGS,
)
from util.docker_helper import get_credential_ip, get_host_ip


def process_docker_compose_template(
    refinery_dir: str, minio_endpoint: str = None
) -> str:
    credential_ip = get_credential_ip()
    cred_endpoint = f"http://{credential_ip}:7053"

    if minio_endpoint is None:
        host_ip = get_host_ip()
        minio_endpoint = f"http://{host_ip}:7053"

    with open(DOCKER_COMPOSE_TEMPLATE, "r") as f:
        template = f.read()

    with open(SERVICE_VERSIONS, "r") as f:
        versions = json.load(f)

    with open(SETTINGS, "r") as f:
        settings = json.load(f)
        for volume, rel_path in settings.items():
            settings[volume] = os.path.normpath(os.path.join(refinery_dir, rel_path))

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
