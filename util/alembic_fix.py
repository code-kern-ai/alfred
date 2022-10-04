from util.constants import PG_CONTAINER
from util.docker_helper import exec_command_on_container, is_container_running
from util.postgres_helper import get_psql_command


def check_revision() -> bool:

    if not is_container_running(PG_CONTAINER):
        return False

    if is_alembic_table_existing():
        return True

    create_alembic_table()

    # check revisions from the newest to the oldest
    if is_revision_87f463aa5112():
        print("Setting revision 87f463aa5112")
        set_revision("87f463aa5112")
    elif is_revision_9618924f9679():
        print("Setting revision 9618924f9679")
        set_revision("9618924f9679")
    elif is_revision_5b3a4deea1c4():
        print("Setting revision 5b3a4deea1c4")
        set_revision("5b3a4deea1c4")
    elif is_revision_992352f4c1f9():
        print("Setting revision 992352f4c1f9")
        set_revision("992352f4c1f9")
    else:
        print("No revision found")
        drop_alembic_table()

    return True


def create_alembic_table():
    exec_command_on_container(
        PG_CONTAINER,
        get_psql_command(
            "CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL, PRIMARY KEY (version_num))"
        ),
    )


def drop_alembic_table():
    exec_command_on_container(
        PG_CONTAINER, get_psql_command("DROP TABLE alembic_version")
    )


def is_alembic_table_existing():
    result = exec_command_on_container(
        PG_CONTAINER,
        get_psql_command(
            "SELECT COUNT(*) FROM  pg_tables WHERE schemaname = 'public' AND tablename  = 'alembic_version';"
        ),
    )
    return result.output.decode("utf-8").strip() != "0"


def is_revision_87f463aa5112():
    result = exec_command_on_container(
        PG_CONTAINER,
        get_psql_command(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='attribute' and column_name='source_code';"
        ),
    )
    return result.output.decode("utf-8").strip() != "0"


def is_revision_9618924f9679():
    result = exec_command_on_container(
        PG_CONTAINER,
        get_psql_command(
            "SELECT COUNT(*) FROM  pg_tables WHERE schemaname = 'public' AND tablename  = 'labeling_access_link';"
        ),
    )
    return result.output.decode("utf-8").strip() != "0"


def is_revision_5b3a4deea1c4():
    result = exec_command_on_container(
        PG_CONTAINER,
        get_psql_command(
            "SELECT COUNT(*) FROM  pg_tables WHERE schemaname = 'public' AND tablename  = 'app_version';"
        ),
    )
    return result.output.decode("utf-8").strip() != "0"


def is_revision_992352f4c1f9():
    result = exec_command_on_container(
        PG_CONTAINER,
        get_psql_command(
            "SELECT COUNT(*) FROM  pg_tables WHERE schemaname = 'public' AND tablename  = 'organization';"
        ),
    )
    return result.output.decode("utf-8").strip() != "0"


def set_revision(revision: str):
    sql = f"INSERT INTO alembic_version VALUES('{revision}')"
    exec_command_on_container(PG_CONTAINER, get_psql_command(sql))
