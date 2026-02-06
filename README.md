# 🤖 AI Automation API

> Backend SaaS API for intelligent workflow orchestration with AI-powered task classification

[![CI](https://github.com/paulopacifico/ai-automation-api/actions/workflows/ci.yml/badge.svg)](https://github.com/paulopacifico/ai-automation-api/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🎯 **Complete CRUD** for task management
- 🤖 **AI-powered classification** - automatic category and priority assignment
- 🔍 **Advanced filtering** - by status, category, priority
- 📄 **Pagination & sorting** - efficient data retrieval
- ✅ **Comprehensive testing** - 24 automated tests with 72% coverage
- 🐳 **Docker-ready** - production-grade containerization
- 🔄 **Database migrations** - Alembic for schema versioning
- 🚀 **CI/CD pipeline** - automated testing and validation
- 📊 **API documentation** - auto-generated with Swagger/ReDoc

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI 0.100+ |
| Language | Python 3.11 |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Testing | pytest + pytest-cov |
| Linting | Ruff |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)

### Running with Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/paulopacifico/ai-automation-api.git
cd ai-automation-api

# Start the services
docker compose up --build

# API will be available at http://localhost:8000
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

## 📡 API Endpoints

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/tasks` | Create a new task (with AI classification) |
| `GET` | `/tasks/{id}` | Get task by UUID |
| `GET` | `/tasks` | List tasks with filters & pagination |
| `PATCH` | `/tasks/{id}` | Update task fields |
| `DELETE` | `/tasks/{id}` | Delete a task |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | API health status |

## 📖 API Documentation

Once the server is running, access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎯 Usage Examples

### Create a Task (with AI Classification)

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication to the API"
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication to the API",
  "status": "pending",
  "category": "development",
  "priority": "high",
  "estimated_duration": 240,
  "created_at": "2026-02-05T15:00:00Z",
  "updated_at": "2026-02-05T15:00:00Z"
}
```

### List Tasks with Filters

```bash
# Filter by status and priority, sorted by creation date
curl "http://localhost:8000/tasks?status=pending&priority=high&sort_by=created_at&sort_order=desc&limit=10"
```

### Update Task Status

```bash
curl -X PATCH http://localhost:8000/tasks/{id} \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

### Delete a Task

```bash
curl -X DELETE http://localhost:8000/tasks/{id}
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_tasks.py -v

# Run linting
ruff check app/
```

## 📊 Query Parameters (GET /tasks)

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `status` | string | Filter by status: `pending`, `processing`, `completed`, `failed` | - |
| `category` | string | Filter by category | - |
| `priority` | string | Filter by priority: `low`, `medium`, `high`, `urgent` | - |
| `limit` | integer | Max results per page (1-100) | 50 |
| `offset` | integer | Number of records to skip | 0 |
| `sort_by` | string | Sort field: `created_at`, `priority`, `status` | `created_at` |
| `sort_order` | string | Sort direction: `asc`, `desc` | `desc` |

## 🗃️ Database Schema

### Task Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key (auto-generated) |
| `title` | String(200) | Task title (required) |
| `description` | String(2000) | Task description (optional) |
| `status` | Enum | `pending`, `processing`, `completed`, `failed` |
| `category` | String | Task category |
| `priority` | String | Task priority |
| `estimated_duration` | Integer | Duration in minutes (1-10080) |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

## 🔧 Configuration

Environment variables (`.env`):

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ai_automation
OPENAI_API_KEY=your_api_key_here  # For AI classification
```

## 🏗️ Project Structure

```
ai-automation-api/
├── app/
│   ├── api/
│   │   └── tasks.py          # Task endpoints
│   ├── models/
│   │   └── task.py           # SQLAlchemy models
│   ├── schemas/
│   │   └── task.py           # Pydantic schemas
│   ├── services/
│   │   └── ai_classifier.py  # AI classification logic
│   ├── database.py           # Database configuration
│   └── main.py               # FastAPI app
├── tests/
│   └── test_tasks.py         # Test suite
├── alembic/                  # Database migrations
├── docker-compose.yml        # Docker services
├── Dockerfile                # Container definition
└── requirements.txt          # Python dependencies
```

## 🚦 CI/CD Pipeline

Automated workflows on every PR:

- ✅ Docker build validation
- ✅ Database migrations test
- ✅ 24 automated tests
- ✅ Code linting (Ruff)
- ✅ Coverage reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

- [ ] JWT Authentication
- [ ] Rate Limiting
- [ ] Redis Caching
- [ ] Webhooks for task events
- [ ] Background job processing
- [ ] Multi-tenancy support
- [ ] GraphQL API
- [ ] Real-time updates (WebSockets)

## 📧 Contact

Paulo Pacifico - [@paulopacifico](https://github.com/paulopacifico)

Project Link: [https://github.com/paulopacifico/ai-automation-api](https://github.com/paulopacifico/ai-automation-api)

---

**Built with ❤️ using FastAPI**
