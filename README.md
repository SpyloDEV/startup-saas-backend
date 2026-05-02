# Startup SaaS Backend

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![CI](https://github.com/SpyloDEV/startup-saas-backend/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SpyloDEV/startup-saas-backend/actions/workflows/ci.yml)

A production-style FastAPI backend for a multi-tenant SaaS product. It includes JWT authentication, workspace membership and roles, project and task APIs, audit logging, background job tracking, Dockerized infrastructure, migrations, CI, and a test suite.

This is designed as a portfolio-grade backend: the structure mirrors the kind of service a startup would use as a foundation for an internal operations tool, customer portal, or lightweight project management product.

## Features

- JWT auth with registration, login, password hashing, and current-user lookup
- Workspace system with `owner`, `admin`, and `member` roles
- Workspace-scoped project CRUD
- Workspace-scoped task CRUD with status, due dates, assignment, pagination, and filters
- Audit logs for important actions such as `user_created`, `workspace_created`, `project_created`, and `task_updated`
- Background job model plus Celery worker for task assignment notifications
- SQLAlchemy 2.0 async database layer with PostgreSQL support
- Alembic migration for the complete schema
- Docker Compose stack with API, PostgreSQL, Redis, and worker services
- Pytest suite covering auth, projects, tasks, and permission rules
- Ruff and Black formatting in local commands and GitHub Actions CI

## Architecture Overview

```mermaid
flowchart LR
    Client["API Client"] --> API["FastAPI App"]
    API --> Routers["Versioned Routers"]
    Routers --> Services["Service Layer"]
    Services --> Repositories["Repository Layer"]
    Repositories --> Postgres["PostgreSQL"]
    Services --> Audit["Audit Log"]
    Services --> Jobs["Background Job Records"]
    Jobs --> Redis["Redis Broker"]
    Redis --> Worker["Celery Worker"]
    Worker --> Postgres
```

The app is intentionally layered:

- `api`: request routing, auth dependencies, pagination, and role guards
- `services`: business rules, audit log creation, task assignment behavior
- `repositories`: database reads and writes
- `models`: SQLAlchemy 2.0 ORM models
- `schemas`: Pydantic request and response contracts
- `workers`: Celery app and background jobs
- `alembic`: migration history
- `tests`: API-level coverage for core workflows

## Tech Stack

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 async ORM
- Alembic
- Redis
- Celery
- JWT with `python-jose`
- Passlib password hashing
- Pytest and HTTPX
- Ruff and Black
- Docker and Docker Compose
- GitHub Actions

## Local Setup

Create a virtual environment and install the project:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Create a local environment file:

```bash
cp .env.example .env
```

Update `.env` with a strong secret:

```bash
SECRET_KEY=$(openssl rand -hex 32)
```

Run migrations:

```bash
make migrate
```

Start the API locally:

```bash
uvicorn app.main:app --reload
```

Open the API docs:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Docker Setup

Run the complete stack:

```bash
cp .env.example .env
make dev
```

Set `SECRET_KEY` in `.env` before using the stack outside local development.

This starts:

- API: http://localhost:8000
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Celery worker

The API container runs Alembic migrations before starting the server.

## Common Commands

```bash
make dev      # Start API, Postgres, Redis, and worker
make test     # Run tests
make lint     # Run Ruff and Black checks
make format   # Format code
make migrate  # Apply Alembic migrations
```

## API Examples

### Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "founder@example.com",
    "password": "strong-password",
    "full_name": "Startup Founder"
  }'
```

Example response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "f580ba6d-a6d9-4d56-8c58-13a9f7c3c8cb",
    "email": "founder@example.com",
    "full_name": "Startup Founder",
    "is_active": true,
    "created_at": "2026-04-28T12:00:00Z"
  }
}
```

### Create a Workspace

```bash
curl -X POST http://localhost:8000/api/v1/workspaces \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Operations"}'
```

### Create a Project

```bash
curl -X POST http://localhost:8000/api/v1/workspaces/$WORKSPACE_ID/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Onboarding",
    "description": "Build the first version of the onboarding workflow."
  }'
```

### Create an Assigned Task

```bash
curl -X POST http://localhost:8000/api/v1/workspaces/$WORKSPACE_ID/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "'"$PROJECT_ID"'",
    "title": "Send welcome email template",
    "status": "todo",
    "due_date": "2026-05-10",
    "assigned_to_id": "'"$USER_ID"'"
  }'
```

### Filter Tasks

```bash
curl "http://localhost:8000/api/v1/workspaces/$WORKSPACE_ID/tasks?status=in_progress&project_id=$PROJECT_ID&limit=20&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

Example response:

```json
{
  "items": [
    {
      "id": "96902e06-08cc-4f14-b4dc-a91e1088a93b",
      "workspace_id": "f119f132-7ff5-4f16-b23f-f6d3c5a4b5fd",
      "project_id": "0f20ed60-1f7f-4867-9fd1-f0ff6ad5168d",
      "title": "Send welcome email template",
      "description": null,
      "status": "in_progress",
      "due_date": "2026-05-10",
      "assigned_to_id": "e785c147-48cb-4e35-b0c1-8ad63845fa11",
      "created_by_id": "f580ba6d-a6d9-4d56-8c58-13a9f7c3c8cb",
      "created_at": "2026-04-28T12:02:11Z",
      "updated_at": "2026-04-28T12:04:30Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

## Folder Structure

```text
.
├── app
│   ├── api
│   │   └── v1
│   ├── core
│   ├── db
│   ├── models
│   ├── repositories
│   ├── schemas
│   ├── services
│   └── workers
├── alembic
│   └── versions
├── tests
├── .github
│   └── workflows
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## Testing

Run the test suite:

```bash
make test
```

Run lint checks:

```bash
make lint
```

The CI workflow runs Ruff, Black, and Pytest against a PostgreSQL service.

## Why This Is Useful For Startups

Most SaaS products need the same backend foundation before they can ship customer-specific value: users, teams, permissions, durable data, background work, auditability, tests, and deployable infrastructure. This project packages those primitives in a clean, extensible structure so a team can add billing, invitations, analytics, domain-specific workflows, or admin tooling without rewriting the core backend.

## Security Notes

- Passwords are hashed before storage.
- JWT secrets are read from environment variables.
- Workspace access is enforced by dependencies and role checks.
- Secrets are not committed. Use `.env.example` as a template only.
- Background jobs are disabled by default in tests and enabled in Docker Compose.

<!-- lead-level-notes:start -->

## Lead-Level Architecture Notes

### Problem

Early SaaS products often outgrow one-off CRUD APIs as soon as workspaces, roles, task ownership, and auditability matter. Teams need a backend that can model tenant boundaries and operational workflows without becoming a tangle of route-level business logic.

### Solution

This backend provides authentication, workspace membership, role-based access, projects, tasks, task assignment, audit logs, and background notification jobs. The service/repository split keeps HTTP routing thin, while PostgreSQL owns relational state and Redis-backed workers handle non-blocking work such as assignment notifications.

### Architecture Overview

This is a portfolio/simulation project, but it is structured around the same boundaries a production team would care about:

- Frontend/client: External clients or frontend apps.
- Backend API: FastAPI routes stay thin and delegate business rules to services.
- Database: PostgreSQL is the source of truth for relational state, ownership, and auditability.
- Redis: Used where the project needs queues, Pub/Sub, cache-ready paths, or rate-limit-ready primitives.
- Background jobs: Task assignment emits a small background job. In a larger product this would move to a durable queue with retry metadata and dead-letter handling.
- Integrations: Mock providers are kept behind service boundaries so real vendors can be added without changing API contracts.
- Runtime flow: Requests validate identity and tenant access first, then call services that persist state, emit logs, and enqueue async work when needed.

Key components:

- FastAPI backend API
- PostgreSQL for users, workspaces, projects, tasks, and audit logs
- Redis broker for background notification jobs
- Worker process for task-assigned email simulation
- JWT authentication and workspace permission checks
- Docker Compose runtime and GitHub Actions CI

### Mermaid Diagrams

#### System Overview

```mermaid
flowchart LR
  Client[API clients] --> API[FastAPI backend]
  SDK[SDKs or integrations] --> API
  API --> DB[(PostgreSQL)]
  API --> Redis[(Redis)]
  API --> Logs[Audit and execution logs]
  Redis --> Async[Workers or realtime consumers]
  Async --> DB
  API --> Mock[Mock external integrations]
```

#### Task Assignment Flow

```mermaid
sequenceDiagram
  participant Client
  participant API
  participant Service as Task service
  participant DB as PostgreSQL
  participant Redis
  participant Worker
  Client->>API: POST /tasks
  API->>Service: Validate workspace role and assignee
  Service->>DB: Insert task and audit log
  Service->>Redis: Enqueue task-assigned notification
  Worker->>DB: Mark notification job outcome
  Client->>API: GET /tasks with filters
```

### Lead-Level Engineering Decisions

- FastAPI keeps the API surface explicit, typed, and easy to document through OpenAPI.
- PostgreSQL is used for durable relational state because the core domain depends on ownership, filtering, constraints, and audit history.
- Service and repository layers keep route handlers small and make permission checks, workflows, and business rules easier to test.
- Redis is used for lightweight async coordination, Pub/Sub, cache-ready access patterns, or rate limiting depending on the product shape.
- Pydantic schemas define clear input/output contracts and avoid leaking ORM details into HTTP responses.
- Docker Compose keeps the local runtime close to a real deployment without hiding the moving parts.
- The project would need Kafka or another event stream when message volume, replay, ordering, or cross-service consumers outgrow Redis queues or Pub/Sub.
- Kubernetes would make sense once multiple API/worker replicas, autoscaling, secrets management, and rollout strategy become operational concerns.
- Object storage becomes necessary when user-uploaded files, exports, or artifacts should not live on local disk.

### Production Considerations

- Rate limiting should be applied to authentication, public ingestion, webhook, and API-key protected endpoints.
- Important POST endpoints should support idempotency keys when clients may retry after timeouts.
- Workers should record retry attempts, terminal failures, and enough context for support/debugging.
- Structured logging should include request IDs, actor IDs, tenant/workspace IDs, and resource IDs where safe.
- Health checks should distinguish process health from dependency readiness for database, Redis, and workers.
- Error responses should stay consistent and avoid leaking internal exception details.
- Pagination and filtering should be mandatory for list endpoints that can grow with customer usage.
- Validation should happen at the API boundary and again inside domain services for sensitive state transitions.
- Audit logs should be append-only from the application's point of view and easy to filter by actor/action/resource.

### Security Considerations

- JWT secrets and database credentials belong in environment variables or a secret manager, never in source code.
- Passwords should be hashed with a slow password hashing algorithm and never logged.
- API keys should be shown only once, stored hashed, scoped to the smallest useful surface, and revocable.
- RBAC or workspace membership checks should happen before returning or mutating tenant-owned resources.
- Tenant/workspace isolation should be tested with explicit cross-tenant access attempts.
- Input validation should cover request bodies, path parameters, uploaded files, and integration payloads.
- Safe defaults matter: deny by default, keep production actions stricter, and prefer explicit allow lists.
- The most important security boundary in this project is workspace isolation and role checks.

### Observability

- Request logs should capture method, path, status, latency, and correlation ID.
- Domain logs should capture state transitions such as queued, processing, completed, failed, revoked, or retried.
- Audit logs explain who changed what and when.
- Metrics/analytics endpoints provide a product-facing view of usage, failure rates, and operational health.
- `/health` gives a basic load balancer check; production would add dependency checks and build/version metadata.
- Error tracking can be mocked locally, but production should send exceptions to Sentry or a similar system.
- Realtime log streams, where present, are for operator feedback and should not replace persisted logs.

### Scaling Strategy

- MVP: one API instance, one PostgreSQL database, one Redis instance, and one worker process is enough to validate the product shape.
- Next step: run multiple API replicas, separate worker queues by workload, and add indexes for tenant ID, status, timestamps, and foreign keys.
- Caching: cache read-heavy reference data carefully and keep invalidation tied to writes or versioned configs.
- Queues: keep short jobs on Redis; move to Kafka, Redpanda, or a managed queue when replay, ordering, or long retention are needed.
- Database: use connection pooling, query plans, and read replicas before introducing unnecessary data stores.
- Horizontal scaling should preserve tenant isolation, idempotency, and clear ownership of background jobs.
- This system would most likely need a stronger event backbone when high-volume task activity or cross-service events.

### Future Improvements

- Add team invitations with expiring tokens
- Add idempotency keys for task creation from integrations
- Add notification delivery receipts and retry dashboards
- Kubernetes manifests or Helm charts once runtime topology matters.
- OpenTelemetry traces across API, workers, database calls, and external integrations.
- Sentry or another error tracker for production exception triage.
- Prometheus and Grafana dashboards for latency, queue depth, throughput, and failure rates.
- More contract and integration tests around permission boundaries and failure paths.

<!-- lead-level-notes:end -->
