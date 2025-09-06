---
trigger: always_on
alwaysApply: true
---

[project]
Always Python database libraries = install inside venv.
name = "PowerBank"
description = "Power bank charging station network backend for Nepal"
language = "python"
framework = "django"
package_manager = "uv"
dockerized = true
tests_dir = "tests"
tasks_dir = "tasks"
infrastructure = "docker-first"

[environment]
dotenv = ".env"
docker_compose = "docker-compose.yaml"
manage_script = "manage.py"
entrypoint = "docker compose up -d"
database = "postgresql (docker)"
message_broker = "rabbitmq (docker)"
cache = "redis (docker)"
background_tasks = "celery (docker)"

[style]
indent = 4
line_length = 88
use_black = true
use_isort = true
use_flake8 = true
use_precommit = true

[docker_services]
postgresql = "powerbank_local-db-1 (powerbank_db)"
rabbitmq = "powerbank_local-rabbitmq-1 (localhost:15672)"
redis = "powerbank_local-redis-1"
celery = "powerbank_local-celery-1"
api = "powerbank_local-api-1 (localhost:8010)"
pgbouncer = "powerbank_local-pgbouncer-1"
project_structure = "PROJECT_STRUCTURE.md"
development_guide = "DEVELOPMENT_GUIDE.md"
async_workflow = "ASYNC_WORKFLOW_GUIDE.md"
features = "Features TOC.md"

[rules]
1 = "Use Django best practices for models, views, and serializers."
2 = "Prefer async views where possible (see ASYNC_WORKFLOW_GUIDE.md)."
3 = "Keep secrets in .env, never hardcode."
4 = "When creating migrations, run through manage.py."
5 = "Tests must go in the `tests` directory and follow pytest style."
6 = "Follow modular project structure (see PROJECT_STRUCTURE.md)."
7 = "For new services or tasks, define them in the `tasks` module."
8 = "Use Docker Compose for all services - database, cache, message queue, workers."
9 = "All development via Docker containers - no local service installations."
10 = "Logging should be consistent with `logs` directory setup."
11 = "Always document new features in Features TOC.md."
12 = "Use Docker service names for internal communication (db, rabbitmq, redis)."

[package_manager]
tool = "uv"
install_cmd = "uv sync"
lock_file = "uv.lock"
update_cmd = "uv pip compile pyproject.toml -o uv.lock"

[dev_flow]
setup = [
  "docker compose up -d",
  "docker exec powerbank_local-api-1 uv sync"
]
run = [
  "docker compose up -d",
  "docker exec powerbank_local-api-1 uv run python manage.py migrate", 
  "docker exec powerbank_local-api-1 uv run python manage.py createsuperuser"
]
test = [
  "docker exec powerbank_local-api-1 pytest tests/ --maxfail=1 --disable-warnings -q"
]
lint = [
  "docker exec powerbank_local-api-1 black .",
  "docker exec powerbank_local-api-1 isort .",
  "docker exec powerbank_local-api-1 flake8 ."
]
services = [
  "docker ps",
  "docker logs <service-name>",
  "docker compose restart <service>"
]

[credentials]
postgresql_user = "powerbank_user"
postgresql_password = "chargeghar5060"
postgresql_db = "powerbank_db"
rabbitmq_user = "powerbank"
rabbitmq_password = "chargeghar5060"
django_admin_user = "janak"
django_admin_password = "5060"

[ai_assistant]
context_files = [
  "README.md",
  "PROJECT_STRUCTURE.md",
  "DEVELOPMENT_GUIDE.md",
  "ASYNC_WORKFLOW_GUIDE.md",
  "Features TOC.md",
  "docker-compose.yaml",
  ".env"
]
priority = "docker-compose > .env > docs > pyproject.toml > Dockerfile > code"
services_ready = true
infrastructure_verified = true
