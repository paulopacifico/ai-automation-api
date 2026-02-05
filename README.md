# 🤖 AI Automation API

> AI-powered automation platform - Backend SaaS API for intelligent workflow orchestration

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Features

- ✅ **RESTful API** with FastAPI
- ✅ **AI-Powered Classification** - Automatic task categorization, priority, and duration estimation
- ✅ **PostgreSQL Database** with SQLAlchemy ORM
- ✅ **Docker Compose** for easy development and deployment
- ✅ **UUID-based** task identification
- ✅ **Async Support** for high performance
- ✅ **Type Safety** with Pydantic schemas

## 📋 API Endpoints

### Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "ok"
}
```

### Create Task
```http
POST /tasks
Content-Type: application/json

{
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication to the API"
}
```
**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication to the API",
  "status": "pending",
  "category": "development",
  "priority": "high",
  "estimated_duration": 180,
  "created_at": "2026-02-04T10:30:00Z",
  "updated_at": "2026-02-04T10:30:00Z"
}
```

### Get Task by ID
```http
GET /tasks/{id}
```
**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication to the API",
  "status": "pending",
  "category": "development",
  "priority": "high",
  "estimated_duration": 180,
  "created_at": "2026-02-04T10:30:00Z",
  "updated_at": "2026-02-04T10:30:00Z"
}
```

### List All Tasks
```http
GET /tasks
```
**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Implement user authentication",
    "status": "pending",
    "category": "development",
    "priority": "high",
    "created_at": "2026-02-04T10:30:00Z"
  }
]
```

## 🛠️ Tech Stack

- **Framework:** FastAPI 0.109
- **Database:** PostgreSQL 15
- **ORM:** SQLAlchemy 2.0
- **AI Integration:** OpenAI GPT / Anthropic Claude
- **Validation:** Pydantic v2
- **Containerization:** Docker & Docker Compose

## 📁 Project Structure

```
ai-automation-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database configuration
│   ├── api/
│   │   ├── __init__.py
│   │   └── tasks.py         # Task endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── task.py          # SQLAlchemy models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── task.py          # Pydantic schemas
│   └── services/
│       ├── __init__.py
│       └── ai_classifier.py # AI classification service
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## 🚦 Getting Started

### Prerequisites

- Docker & Docker Compose
- OpenAI API Key OR Anthropic API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/paulopacifico/ai-automation-api.git
   cd ai-automation-api
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Start the services**
   ```bash
   docker-compose up --build
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## ⚙️ Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | `postgresql://postgres:postgres@postgres:5432/automation` |
| `OPENAI_API_KEY` | OpenAI API key for classification | Yes* | - |
| `ANTHROPIC_API_KEY` | Anthropic API key for classification | Yes* | - |
| `APP_ENV` | Application environment | No | `development` |
| `LOG_LEVEL` | Logging level | No | `info` |
| `API_TIMEOUT` | AI API request timeout (seconds) | No | `10` |

*Choose either OpenAI or Anthropic

## 🧪 Testing

```bash
# Run tests (coming soon)
docker-compose exec api pytest

# Run with coverage
docker-compose exec api pytest --cov=app
```

## 📊 AI Classification

The API automatically classifies tasks using AI based on title and description:

- **Category:** Type of task (e.g., development, bug-fix, documentation)
- **Priority:** Urgency level (low, medium, high)
- **Estimated Duration:** Time estimate in minutes

### Example Classification

**Input:**
```json
{
  "title": "Fix critical security vulnerability in auth module",
  "description": "CVE-2024-1234 - SQL injection in login endpoint"
}
```

**AI Classification:**
```json
{
  "category": "security",
  "priority": "high",
  "estimated_duration": 240
}
```

## 🔧 Development

### Running Locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set up database
createdb automation

# Run migrations (if using Alembic)
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for the powerful ORM
- [OpenAI](https://openai.com/) / [Anthropic](https://anthropic.com/) for AI capabilities

## 📧 Contact

Paulo Pacifico - [@paulopacifico](https://github.com/paulopacifico)

Project Link: [https://github.com/paulopacifico/ai-automation-api](https://github.com/paulopacifico/ai-automation-api)

---

**Built with ❤️ using FastAPI and AI**
