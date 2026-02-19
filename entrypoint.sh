#!/bin/sh

# Esperar DB ficar pronto
echo "Aguardando banco de dados..."
# sleep 5 # Em produção usar wait-for-it.sh

# Rodar migrations
echo "Aplicando migrations..."
alembic upgrade head

# Criar tabelas e dados iniciais
echo "Criando tabelas..."
python -m app.create_tables
echo "Populando dados iniciais..."
python -m app.initial_data

# Iniciar aplicação usando gunicorn para produção
echo "Iniciando servidor na porta ${PORT:-8000}..."
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:${PORT:-8000}
