import docker
import json
import os
import time
from typing import Any, Tuple

from util.constants import (
    EXEC_ENVS,
    SERVICE_VERSIONS,
    JWKS_PATH,
    POSTGRES_MIGRATE_CONTAINER,
    REFINERY,
)

client = docker.from_env()


def check_and_pull_exec_env_images() -> None:
    with open(SERVICE_VERSIONS, "r") as f:
        versions = json.load(f)[REFINERY]

    for exec_env, image_name in EXEC_ENVS.items():
        image_tag = versions[exec_env]
        if not is_image_present(image_name, image_tag):
            client.images.pull(image_name, image_tag)
            print(f"pulled {image_name}:{image_tag}")


def create_jwks_secret_if_not_existing() -> None:

    if os.path.isfile(JWKS_PATH):
        with open(JWKS_PATH, "r") as f:
            line = f.readline().strip()
            if len(line) != 0:
                return

    if not is_image_present("docker.io/oryd/oathkeeper", "v0.38"):
        client.images.pull("docker.io/oryd/oathkeeper", "v0.38")

    jwks = client.containers.run(
        "docker.io/oryd/oathkeeper:v0.38",
        "credentials generate --alg RS256",
        remove=True,
    )
    with open(JWKS_PATH, "w") as f:
        f.write(jwks.decode("utf-8"))


def exec_command_on_container(container_name: str, command: str) -> Tuple[int, Any]:
    container = client.containers.list(filters={"name": container_name})[0]
    return container.exec_run(command)


def get_credential_ip() -> str:
    network = client.networks.get("bridge")
    return network.attrs["IPAM"]["Config"][0]["Gateway"]


def is_container_running(container_name: str) -> bool:
    try:
        container = client.containers.list(filters={"name": container_name})[0]
        return container.status == "running"
    except Exception:
        return False


def is_image_present(image_name: str, image_tag: str) -> bool:
    try:
        client.images.get(f"{image_name}:{image_tag}")
    except docker.errors.ImageNotFound:
        return False
    return True


def is_uvicorn_application_started(container_name: str) -> bool:
    try:
        container = client.containers.list(filters={"name": container_name})[0]
        return "Application startup complete." in container.logs().decode("utf-8")
    except IndexError:
        return False


def is_ui_service_ready(container_name: str) -> bool:
    try:
        container = client.containers.list(filters={"name": container_name})[0]
        return "Configuration complete; ready for start up" in container.logs().decode(
            "utf-8"
        )
    except IndexError:
        return False


def wait_until_postgres_migration_is_exited(timeout: int = 600) -> bool:
    start_time = time.time()

    while start_time + timeout > time.time():
        try:
            container = client.containers.list(
                filters={"name": POSTGRES_MIGRATE_CONTAINER}
            )[0]
            if container.status == "exited":
                return True
        except Exception:
            return False
        time.sleep(1)
    return False


def wait_until_refinery_is_ready(timeout: int = 60) -> bool:
    start_time = time.time()

    while start_time + timeout > time.time():
        gateway_ready = is_uvicorn_application_started("refinery-gateway")
        ui_ready = is_ui_service_ready("refinery-ui")
        if gateway_ready and ui_ready:
            return True
        time.sleep(1)
    return False
