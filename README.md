# AI Automation API

Backend API for AI-assisted task orchestration. Create tasks, auto-classify them with a large language model, and manage the lifecycle with robust filtering and pagination.

[![CI](https://github.com/paulopacifico/ai-automation-api/actions/workflows/ci.yml/badge.svg)](https://github.com/paulopacifico/ai-automation-api/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This project demonstrates a production-style backend with clean domain boundaries, AI provider integration, and a reproducible development workflow. It is intentionally scoped but covers the core concerns of a SaaS API: persistence, validation, observability through logs, and automated quality checks.

## Key Capabilities

- Task CRUD with status tracking
- AI-driven classification of category, priority, and estimated duration
- Filtered task listing with sorting and pagination
- Database migrations with Alembic
- Dockerized local environment (API + PostgreSQL)
- CI pipeline for build, migrations, tests, and lint

## Engineering Highlights

- Provider-agnostic AI classification (OpenAI or Anthropic) with safe fallbacks
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
DATABASE_URL=postgresql://user:password@localhost:5432/ai_automation
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

Notes:

- If both `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` are set, OpenAI is used.
- If no provider key is configured or an AI call fails, the API falls back to defaults (category `general`, priority `medium`, estimated_duration `30`).

## API Endpoints

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/tasks` | Create a task (classification applied on create) |
| `GET` | `/tasks/{id}` | Fetch a task by UUID |
| `GET` | `/tasks` | List tasks with filters, sorting, pagination |
| `PATCH` | `/tasks/{id}` | Update task fields |
| `DELETE` | `/tasks/{id}` | Delete a task |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | API health status |

## API Documentation

Once running, explore:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Usage Examples

### Create a Task (AI Classification)

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication to the API"
  }'
```

Example response:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication to the API",
  "status": "pending",
  "category": "general",
  "priority": "medium",
  "estimated_duration": 30,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### List Tasks with Filters

```bash
curl "http://localhost:8000/tasks?status=pending&priority=high&sort_by=created_at&sort_order=desc&limit=10"
```

### Update Task Status

```bash
curl -X PATCH http://localhost:8000/tasks/{id} \
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
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # AI classification logic
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

- JWT authentication
- Rate limiting
- Redis caching
- Webhooks for task events
- Background job processing
- Multi-tenancy support
- GraphQL API
- Real-time updates (WebSockets)

## Contact

Paulo Pacifico - [@paulopacifico](https://github.com/paulopacifico)

Project: [github.com/paulopacifico/ai-automation-api](https://github.com/paulopacifico/ai-automation-api)

Built with FastAPI.
