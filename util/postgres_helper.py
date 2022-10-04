import time
from util.constants import CONNECTION_STRING, PG_CONTAINER
from util.docker_helper import exec_command_on_container


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
