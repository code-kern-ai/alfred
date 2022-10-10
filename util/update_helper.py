import json
import time
from typing import List
from util.constants import SERVICE_VERSIONS
from util.docker_helper import is_uvicorn_application_started, exec_command_on_container
from util.postgres_helper import get_db_versions, wait_until_postgres_is_ready


def is_any_service_version_changed() -> bool:
    with open(SERVICE_VERSIONS, "r") as f:
        current_versions = json.load(f)

    db_versions = get_db_versions()

    any_service_updated = False
    for service, version in db_versions.items():
        if is_newer(current_versions[service].lstrip("v"), version):
            any_service_updated = True
            break
    return any_service_updated


# v1 newer than v2 (e.g. 1.1.2 > 1.1.1)
def is_newer(v1: str, v2: str) -> bool:
    a = [int(x) for x in v1.split(".")]
    b = [int(x) for x in v2.split(".")]
    if len(a) != len(b) and len(a) != 3:
        raise Exception("invalid version format")
    return __is_newer_int(a, b)


def __is_newer_int(v1: List[int], v2: List[int]) -> bool:
    for idx, _ in enumerate(v1):
        if v2[idx] > v1[idx]:
            return False
        elif v2[idx] < v1[idx]:
            return True
    return False


def updater_service_update_to_newest():
    # the updater service is part of the docker-compose stack and therefore located
    # in a differrent network than alfred. Therefore, the updater service can not
    # be reached via the alfred network. Therefore, we need to use the docker
    # exec command to update the updater service.
    # The following command executes the update_to_current command on the updater service.
    exit_code, output = exec_command_on_container(
        "refinery-updater", "python -c 'import app; app.update_to_newest()'"
    )
    if exit_code == 0:
        return True, output
    print("Update failed!", flush=True)
    return False, output


def wait_until_updater_is_ready(timeout: int = 300) -> bool:
    start_time = time.time()

    while start_time + timeout > time.time():
        if is_uvicorn_application_started("refinery-updater"):
            return True
    return False


def wait_until_db_and_updater_service_are_ready() -> bool:
    if wait_until_postgres_is_ready():
        if is_uvicorn_application_started("refinery-updater"):
            return True
        else:
            return wait_until_updater_is_ready()
    return False
