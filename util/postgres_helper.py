import os
import time
from datetime import datetime
from util.constants import BACKUP_DIR, CONNECTION_STRING, PG_CONTAINER
from util.docker_helper import exec_command_on_container


def create_database_dump():
    exit_code, result = exec_command_on_container(
        PG_CONTAINER, f"pg_dump -d {CONNECTION_STRING}"
    )
    if exit_code != 0:
        return False

    now = datetime.now()
    timestamp = now.strftime("%m_%d_%Y_%H_%M_%S")
    backup_path = os.path.join(BACKUP_DIR, f"db_dump_{timestamp}.sql")

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    with open(backup_path, "wb") as f:
        f.write(result)

    return True


def get_psql_command(sql: str):
    return f'psql -d {CONNECTION_STRING} -c "{sql}" -qtAX'


def wait_until_postgres_is_ready(timeout: int = 300):
    start_time = time.time()

    while start_time + timeout > time.time():
        exit_code, _ = exec_command_on_container(PG_CONTAINER, "pg_isready")
        if exit_code == 0:
            return True
        time.sleep(1)
    return False


def get_db_versions():
    exit_code, result = exec_command_on_container(
        PG_CONTAINER,
        get_psql_command("SELECT service, installed_version FROM app_version"),
    )
    versions = {}
    if exit_code == 0:
        result = result.decode("utf-8")
        for line in result.splitlines():
            service, installed_version = line.split("|")
            versions[service] = installed_version
    return versions
