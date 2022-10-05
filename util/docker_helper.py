import docker
import json
import os
import socket
import time
from typing import Any, Tuple

from util.constants import EXEC_ENVS, SERVICE_VERSIONS, JWKS_PATH

client = docker.from_env()


def check_and_pull_exec_env_images() -> None:
    with open(SERVICE_VERSIONS, "r") as f:
        versions = json.load(f)

    for exec_env, image_name in EXEC_ENVS.items():
        image_tag = versions[exec_env]
        if not is_image_present(image_name, image_tag):
            client.images.pull(image_name, image_tag)
            print(f"pulled {image_name}:{image_tag}")


def create_jwks_secret_if_not_existing() -> None:

    if os.path.isfile(JWKS_PATH):
        return

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


def get_host_ip() -> str:
    # https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(("10.254.254.254", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


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
    except docker.errors.ImageNotFound:
        return False


def is_ui_service_ready(container_name: str) -> bool:
    try:
        container = client.containers.list(filters={"name": container_name})[0]
        return "Configuration complete; ready for start up" in container.logs().decode(
            "utf-8"
        )
    except docker.errors.ImageNotFound:
        return False


def wait_until_refinery_is_ready(timeout: int = 60) -> None:
    start_time = time.time()

    while start_time + timeout > time.time():
        gateway_ready = is_uvicorn_application_started("refinery-gateway")
        ui_ready = is_ui_service_ready("refinery-ui")
        if gateway_ready and ui_ready:
            return True
        time.sleep(1)
    return False
