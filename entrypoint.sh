#!/bin/sh

# Esperar DB ficar pronto
echo "Aguardando banco de dados..."
# sleep 5 # Em produção usar wait-for-it.sh

# Rodar migrations
echo "Aplicando migrations..."
alembic upgrade head

# Criar dados iniciais (opcional, pode ser script separado)
# python initial_data.py

# Iniciar aplicação usando gunicorn para produção
echo "Iniciando servidor na porta ${PORT:-8000}..."
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:${PORT:-8000}
