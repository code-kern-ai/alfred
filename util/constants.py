# paths are inside the container so the volume needs to be connected
BACKUP_DIR = "/refinery/backup"
CONNECTION_STRING = "postgresql://postgres:onetask@graphql-postgres:5432"
DOCKER_COMPOSE = "/refinery/docker-compose.yml"
DOCKER_COMPOSE_TEMPLATE = "templates/docker-compose.yml"
EXEC_ENVS = {
    "AC_EXEC_ENV": "kernai/refinery-ac-exec-env",
    "ML_EXEC_ENV": "kernai/refinery-ml-exec-env",
    "LF_EXEC_ENV": "kernai/refinery-lf-exec-env",
    "RECORD_IDE_ENV": "kernai/refinery-record-ide-env",
}
JWKS_PATH = "/refinery/oathkeeper/jwks.json"
PG_CONTAINER = "graphql-postgres"
POSTGRES_MIGRATE_CONTAINER = "postgres-migrate"
REFINERY = "REFINERY"
SERVICE_VERSIONS = "/refinery/versions.json"
SETTINGS = "/refinery/settings.json"
THIRD_PARTY = "THIRD_PARTY"
