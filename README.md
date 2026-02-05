# AI Automation API

Backend API for AI-assisted task automation and classification.

## Features
- REST API with FastAPI
- PostgreSQL persistence via SQLAlchemy
- AI-powered task classification (category, priority, duration)
- Docker Compose for local development

## API Endpoints
### Health Check
```http
GET /health
```
Response:
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
Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication to the API",
  "status": "pending",
  "category": "development",
  "priority": "high",
  "estimated_duration": 180,
  "created_at": "2026-02-05T10:30:00Z",
  "updated_at": "2026-02-05T10:30:00Z"
}
```

### Get Task by ID
```http
GET /tasks/{id}
```

### List Tasks
```http
GET /tasks
```

## Tech Stack
- Python 3.11
- FastAPI
- SQLAlchemy
- PostgreSQL
- OpenAI / Anthropic
- Docker

## Getting Started (Docker)
1. Set environment variables (example below)
2. Start services:
   ```bash
   docker compose up --build
   ```
3. API: `http://localhost:8000`
4. Docs: `http://localhost:8000/docs`

## Environment Variables
Required:
- `DATABASE_URL`
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

Optional:
- `APP_ENV`
- `LOG_LEVEL`
- `API_TIMEOUT`
- `MAX_RETRIES`

## Project Structure
```
ai-automation-api/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── api/
│   │   └── tasks.py
│   ├── models/
│   │   └── task.py
│   ├── schemas/
│   │   └── task.py
│   └── services/
│       └── ai_classifier.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## AI Classification
Tasks are automatically classified from title and description:
- `category`: task domain (e.g., development, docs, security)
- `priority`: low | medium | high
- `estimated_duration`: minutes

If the AI provider fails, default values are used and the task is still created.
