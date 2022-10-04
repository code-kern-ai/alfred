from fastapi import FastAPI, responses, status
from util.alembic_fix import check_revision
from util.docker_helper import (
    create_jwks_secret_if_not_existing,
    check_and_pull_exec_env_images,
)
from util.postgres_helper import wait_until_postgres_is_ready
from util.template_processor import process_docker_compose_template

app = FastAPI()


@app.get("/start")
def manage_refinery_start():
    minio_endpoint = process_docker_compose_template()
    create_jwks_secret_if_not_existing()
    check_and_pull_exec_env_images()
    if wait_until_postgres_is_ready():
        check_revision()
    else:
        return responses.Response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content="Postgres is not ready",
        )
    return responses.HTMLResponse(
        status_code=status.HTTP_200_OK, content=minio_endpoint
    )


@app.get("/app_ready")
def check_if_app_is_ready():
    return responses.HTMLResponse(status_code=status.HTTP_200_OK)


@app.get("/update")
def manage_refinery_update():
    return "Update"
