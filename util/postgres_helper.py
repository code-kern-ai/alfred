import json
import os
import time
from datetime import datetime
from typing import Dict
from zipfile import ZipFile
from util.constants import BACKUP_DIR, CONNECTION_STRING, PG_CONTAINER, SERVICE_VERSIONS
from util.docker_helper import exec_command_on_container


def create_database_dump() -> bool:
    exit_code, result = exec_command_on_container(
        PG_CONTAINER, f"pg_dump -d {CONNECTION_STRING}"
    )
    if exit_code != 0:
        return False

    now = datetime.now()
    timestamp = now.strftime("%m_%d_%Y_%H_%M_%S")
    backup_zip = os.path.join(BACKUP_DIR, f"db_dump_{timestamp}.zip")
    backup_fname = os.path.join(BACKUP_DIR, f"db_dump_{timestamp}.sql")

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    with ZipFile(backup_zip, "w") as zf:
        zf.writestr(backup_fname, result)

    return True


def get_psql_command(sql: str) -> str:
    return f'psql -d {CONNECTION_STRING} -c "{sql}" -qtAX'


def wait_until_postgres_is_ready(timeout: int = 300) -> bool:
    start_time = time.time()

    while start_time + timeout > time.time():
        exit_code, _ = exec_command_on_container(PG_CONTAINER, "pg_isready")
        if exit_code == 0:
            return True
        time.sleep(1)
    return False


def get_db_versions() -> Dict[str, str]:
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


def update_db_versions() -> bool:

    with open(SERVICE_VERSIONS, "r") as f:
        current_versions = json.load(f)
    db_versions = get_db_versions()

    # update existing service versions
    sql_commands = []
    for service, db_version in db_versions.items():
        current_version = current_versions[service].lstrip("v")
        if current_version != db_version:
            sql_commands.append(
                f"""
                UPDATE app_version
                SET installed_version = '{current_version}'
                WHERE service = '{service}';
                """
            )
    if sql_commands:
        exit_code, _ = exec_command_on_container(
            PG_CONTAINER,
            get_psql_command("\n".join(sql_commands)),
        )
        if exit_code != 0:
            return False

    # add new service versions
    for service, version in current_versions.items():
        if service not in db_versions:
            sql_commands.append(
                f"""
                INSERT INTO app_version (service, installed_version)
                VALUES ('{service}', '{version.lstrip("v")}');
                """
            )
    if sql_commands:
        exit_code, _ = exec_command_on_container(
            PG_CONTAINER, get_psql_command("\n".join(sql_commands))
        )
        if exit_code != 0:
            return False
    return True
