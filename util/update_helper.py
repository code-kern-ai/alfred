import json
import time
from util.constants import SERVICE_VERSIONS
from util.docker_helper import is_uvicorn_application_started, exec_command_on_container
from util.postgres_helper import get_db_versions, wait_until_postgres_is_ready


def is_any_service_version_changed() -> bool:
    with open(SERVICE_VERSIONS, "r") as f:
        current_versions = json.load(f)

    db_versions = get_db_versions()

    any_service_updated = False
    for service, version in db_versions.items():
        db_version_int = _version_number_to_int(version)
        current_version_int = _version_number_to_int(current_versions[service])

        if db_version_int < current_version_int:
            any_service_updated = True
        elif db_version_int > current_version_int:
            print(
                f"Last version of {service} is newer than current version! Cannot update!",
                flush=True,
            )
            return False
    return any_service_updated


def _version_number_to_int(version_number: str) -> int:
    return int(version_number.lstrip("v").replace(".", ""))


def updater_service_update_to_newest():
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
