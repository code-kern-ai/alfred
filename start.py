import subprocess
import sys
from util.alembic_fix import check_revision
from util.constants import DOCKER_COMPOSE
from util.docker_helper import (
    create_jwks_secret_if_not_existing,
    check_and_pull_exec_env_images,
    wait_until_refinery_is_ready,
)
from util.postgres_helper import wait_until_postgres_is_ready
from util.template_processor import process_docker_compose_template

refinery_dir = sys.argv[1]

print("Creating docker-compose.yml file...", flush=True)
minio_endpoint = process_docker_compose_template(refinery_dir)
print("Creating jwks.json secret...", flush=True)
create_jwks_secret_if_not_existing()
print("Checking and pulling exec env images...", flush=True)
check_and_pull_exec_env_images()

print("Starting postgres container...", flush=True)
subprocess.call(
    ["docker-compose", "-f", DOCKER_COMPOSE, "up", "-d", "graphql-postgres"]
)
print("Waiting for postgres to be ready...", flush=True)
if wait_until_postgres_is_ready():
    check_revision()

print("Starting all containers...", flush=True)
subprocess.call(["docker-compose", "-f", DOCKER_COMPOSE, "up", "-d"])


print("Checking if all services are ready...", flush=True)
if wait_until_refinery_is_ready():
    print("Refinery is ready!", flush=True)
else:
    print("Refinery is not ready!", flush=True)

print("UI:           http://localhost:4455/app/")
print(f"Minio:        {minio_endpoint}")
print("MailHog:      http://localhost:4436/")
