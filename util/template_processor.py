import json
import sys

from util.constants import (
    DOCKER_COMPOSE,
    DOCKER_COMPOSE_TEMPLATE,
    SERVICE_VERSIONS,
    SETTINGS,
)
from util.docker_helper import get_credential_ip, get_host_ip


def process_docker_compose_template(refinery_dir: str, is_windows: bool) -> str:
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
        path_sep = "\\" if is_windows else "/"
        for volume, path in settings.items():
            if path.startswith(".."):
                print("Path in settings.json must not start with '..'!", flush=True)
                sys.exit(1)
            if refinery_dir[0] == ".":  # relative path
                path = path[1:]
                if path[0] != path_sep:
                    path = path_sep + path[1:]
                settings[volume] = refinery_dir + path
            else:
                settings[volume] = path

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
