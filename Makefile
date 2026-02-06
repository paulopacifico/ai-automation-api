.PHONY: help up down reset test migrate shell logs clean seed-admin worker-up worker-logs

help: ## Mostrar este help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Subir containers
	docker-compose up -d

down: ## Parar containers
	docker-compose down

reset: ## Resetar banco de dados (limpa volumes!)
	docker-compose down -v
	docker-compose up -d postgres
	@echo "Aguardando PostgreSQL..."
	@sleep 5
	docker-compose run --rm api alembic upgrade head
	docker-compose up -d api
	@echo "✅ Banco resetado!"

test: ## Rodar testes
	docker-compose exec api pytest -v

test-cov: ## Rodar testes com coverage
	docker-compose exec api pytest -v --cov=app --cov-report=term-missing

migrate: ## Rodar migrations
	docker-compose exec api alembic upgrade head

migration: ## Criar nova migration (use: make migration msg="mensagem")
	docker-compose exec api alembic revision --autogenerate -m "$(msg)"

shell: ## Abrir shell no container da API
	docker-compose exec api /bin/bash

psql: ## Conectar ao PostgreSQL
	docker-compose exec postgres psql -U postgres -d postgres

logs: ## Ver logs da API
	docker-compose logs -f api

worker-up: ## Subir worker de classificacao
	docker-compose up -d worker

worker-logs: ## Ver logs do worker
	docker-compose logs -f worker

clean: ## Limpar caches Python
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

lint: ## Rodar linter
	docker-compose exec api ruff check app/

format: ## Formatar código
	docker-compose exec api ruff format app/

seed-admin: ## Criar/promover usuario admin (use: make seed-admin ADMIN_EMAIL=... ADMIN_PASSWORD=...)
	docker-compose run --rm api python -m app.scripts.seed_admin
