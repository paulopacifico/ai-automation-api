# AI Automation API

Backend API for AI-assisted task orchestration. Create tasks, auto-classify them with a large language model, and manage the lifecycle with robust filtering and pagination.

[![CI](https://github.com/paulopacifico/ai-automation-api/actions/workflows/ci.yml/badge.svg)](https://github.com/paulopacifico/ai-automation-api/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This project demonstrates a production-style backend with clean domain boundaries, Hugging Face integration, and a reproducible development workflow. It is intentionally scoped but covers the core concerns of a SaaS API: persistence, validation, observability through logs, and automated quality checks.

## Key Capabilities

- Task CRUD with status tracking
- AI-driven classification of category, priority, and estimated duration
- Filtered task listing with sorting and pagination
- Database migrations with Alembic
- Dockerized local environment (API + PostgreSQL)
- CI pipeline for build, migrations, tests, and lint

## Engineering Highlights

- Hugging Face zero-shot classification with safe fallbacks
- Clear API/data boundaries using FastAPI, Pydantic, and SQLAlchemy
- Reproducible development stack with Docker Compose
- CI validates build, migrations, tests, and lint on every push/PR

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI |
| Language | Python 3.11 |
| Database | PostgreSQL 16 (Docker) |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Testing | pytest + pytest-cov |
| Linting | Ruff |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Run with Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/paulopacifico/ai-automation-api.git
cd ai-automation-api

# Configure environment
cp .env.example .env
# Edit .env and set strong values for JWT_SECRET_KEY, POSTGRES_PASSWORD, REDIS_PASSWORD

# Start the services
docker compose up --build

# API available at http://localhost:8000
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database (requires PostgreSQL running)
alembic upgrade head

# Run the server
uvicorn app.main:app --reload
```

## Configuration

Environment variables (via shell or `.env`):

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
POSTGRES_DB=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql://user:password@localhost:5432/ai_automation
REDIS_PASSWORD=
REDIS_PORT=6379
REDIS_URL=redis://:your-redis-password@localhost:6379/0
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_AUTH=10/minute
TASK_CLASSIFICATION_MODE=async
TASK_QUEUE_NAME=task-classification
TASK_QUEUE_RETRY_MAX=3
ENV=development
API_PORT=8000
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token
HF_MODEL_ID=MoritzLaurer/mDeBERTa-v3-base-mnli-xnli
HF_TIMEOUT_SECONDS=20
HF_MAX_RETRIES=3
```

Notes:

- `JWT_SECRET_KEY` is required and must be strong outside development. Generate one with `openssl rand -base64 48`.
- `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, and `JWT_SECRET_KEY` are mandatory for Docker Compose and fail fast when missing.
- Docker Compose now binds API, PostgreSQL, and Redis ports to `127.0.0.1` by default.
- For production deployments, prefer managed Redis/PostgreSQL with TLS enabled (`rediss://` for Redis where supported).
- If `HUGGINGFACEHUB_API_TOKEN` is not configured or an inference call fails, the API falls back to defaults (category `general`, priority `medium`, estimated_duration `30`).
- The default model is `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` and can be overridden with `HF_MODEL_ID`.
- Rate limiting uses in-memory storage if `REDIS_URL` is not set. Use Redis for multi-instance deployments.
- `TASK_CLASSIFICATION_MODE=async` uses Redis + RQ worker. Use `sync` for local debug and tests.

## Background Worker

Run API + worker with Docker Compose:

```bash
docker compose up --build
```

Run worker only:

```bash
docker compose up -d worker
docker compose logs -f worker
```

## Admin User Seed

Create or promote an admin user locally:

```bash
ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=ChangeMe123 \
  docker compose run --rm api python -m app.scripts.seed_admin
```

Notes:

- If the user exists, the script sets role to `admin` and resets the password.

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register a user |
| `POST` | `/auth/login` | Obtain access and refresh tokens |
| `POST` | `/auth/refresh` | Rotate refresh token |
| `POST` | `/auth/logout` | Revoke refresh token |
| `GET` | `/auth/me` | Get current user profile |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/tasks` | Create a task (auth required) |
| `GET` | `/tasks/{id}` | Fetch a task by UUID (auth required) |
| `GET` | `/tasks` | List tasks with filters, sorting, pagination (auth required) |
| `PATCH` | `/tasks/{id}` | Update task fields (auth required) |
| `DELETE` | `/tasks/{id}` | Delete a task (auth required) |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | API health status |
| `GET` | `/health/live` | Liveness check |
| `GET` | `/health/ready` | Readiness check (DB and Redis) |

## API Documentation

Once running, explore:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Usage Examples

### Register a User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "ChangeMe123"
  }'
```

### Login and Store Token

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"ChangeMe123"}' | \
  python -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')
```

### Create a Task (AI Classification)

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication to the API"
  }'
```

### List Tasks with Filters

```bash
curl "http://localhost:8000/tasks?status=pending&priority=high&sort_by=created_at&sort_order=desc&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Update Task Status

```bash
curl -X PATCH http://localhost:8000/tasks/{id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

## Query Parameters (GET /tasks)

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `status` | string | `pending`, `processing`, `completed`, `failed` | - |
| `category` | string | Filter by category | - |
| `priority` | string | Filter by priority (commonly `low`, `medium`, `high`, `urgent`) | - |
| `limit` | integer | Max results per page (1-100) | 50 |
| `offset` | integer | Records to skip | 0 |
| `sort_by` | string | `created_at`, `priority`, `status` | `created_at` |
| `sort_order` | string | `asc`, `desc` | `desc` |

## Data Model (Task)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key (auto-generated) |
| `title` | string | Required, max 200 chars (API validation) |
| `description` | string | Optional, max 2000 chars (API validation) |
| `status` | enum | `pending`, `processing`, `completed`, `failed` |
| `category` | string | AI-derived on create, editable via PATCH |
| `priority` | string | AI-derived on create, editable via PATCH |
| `estimated_duration` | integer | Minutes (1-10080) |
| `owner_id` | UUID | Task owner (set from authenticated user) |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

## Testing

```bash
pytest
pytest --cov=app --cov-report=html
pytest tests/test_tasks.py -v
ruff check app/
```

## Project Structure

```
ai-automation-api/
├── app/
│   ├── api/                  # Route handlers
│   ├── jobs/                 # RQ background jobs
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # AI services and queue integration
│   ├── database.py           # DB configuration
│   └── main.py               # FastAPI app
├── tests/                    # Test suite
├── alembic/                  # Database migrations
├── docker-compose.yml        # Docker services
├── Dockerfile                # Container definition
└── requirements.txt          # Python dependencies
```

## CI Pipeline

Automated checks on every push/PR:

- Docker image build
- Database migrations
- Test suite
- Linting (Ruff)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

- JWT authentication (implemented)
- Rate limiting (implemented)
- Background job processing (implemented with Redis + RQ)
- Redis caching
- Webhooks for task events
- Multi-tenancy support
- GraphQL API
- Real-time updates (WebSockets)

## Contact

Paulo Pacifico - [@paulopacifico](https://github.com/paulopacifico)

Project: [github.com/paulopacifico/ai-automation-api](https://github.com/paulopacifico/ai-automation-api)

Built with FastAPI.
