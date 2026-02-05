# ai-automation-api

API para automação de tarefas com FastAPI.

## Stack
- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy

## Como rodar com Docker
1. `docker compose up --build`
2. A API ficará disponível em `http://localhost:8000`

## Endpoint
- `GET /health` retorna `{"status": "ok"}`
