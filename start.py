import subprocess
import sys
from util.alembic_fix import check_revision
from util.constants import DOCKER_COMPOSE
from util.docker_helper import (
    create_jwks_secret_if_not_existing,
    check_and_pull_exec_env_images,
    wait_until_refinery_is_ready,
)
from util.postgres_helper import create_database_dump, wait_until_postgres_is_ready
from util.template_processor import process_docker_compose_template
from util.update_helper import (
    is_any_service_version_changed,
    updater_service_update_to_newest,
    wait_until_db_and_updater_service_are_ready,
)

refinery_dir = sys.argv[1]

if wait_until_refinery_is_ready(timeout=1):
    print("Refinery is already running!", flush=True)
    sys.exit(0)

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

run_updates = is_any_service_version_changed()
if run_updates:
    success_db_dump = create_database_dump()
    if not success_db_dump:
        print("Database dump failed!", flush=True)
        print("Please contact the developers!", flush=True)
        sys.exit(0)

print("Starting all containers...", flush=True)
subprocess.call(["docker-compose", "-f", DOCKER_COMPOSE, "up", "-d"])

wait_until_db_and_updater_service_are_ready()
if run_updates:
    print("Service versions have changed.", flush=True)
    print("Trigger the updater service to run database updates...", flush=True)
    success, output = updater_service_update_to_newest()
    if success:
        print("Update successful!", flush=True)
    else:
        print("Update failed!", flush=True)
        print(output, flush=True)

print("Checking if all services are ready...", flush=True)
if wait_until_refinery_is_ready():
    print("Refinery is ready!", flush=True)
else:
    print("Refinery is not ready!", flush=True)

print("UI:           http://localhost:4455/app/")
print(f"Minio:        {minio_endpoint}")
print("MailHog:      http://localhost:4436/")
