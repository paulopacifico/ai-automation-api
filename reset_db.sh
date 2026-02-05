#!/bin/bash
# reset_db.sh - Script para resetar banco de dados local

set -e

echo "🔄 Resetando banco de dados local..."

# Parar containers
echo "1️⃣ Parando containers..."
docker-compose down -v

# Subir novamente
echo "2️⃣ Subindo containers..."
docker-compose up -d postgres

# Aguardar postgres estar pronto
echo "3️⃣ Aguardando PostgreSQL..."
sleep 5

# Rodar migrations
echo "4️⃣ Rodando migrations..."
docker-compose run --rm api alembic upgrade head

# Subir API
echo "5️⃣ Subindo API..."
docker-compose up -d api

echo "✅ Banco resetado com sucesso!"
echo "📡 API disponível em http://localhost:8000"
echo "🧪 Rode os testes com: docker-compose exec api pytest -v"
