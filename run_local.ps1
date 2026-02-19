# SisCont Local Setup Script

Write-Host "Iniciando configuração local do SisCont..." -ForegroundColor Cyan

# 1. Criar ambiente virtual
if (!(Test-Path "venv")) {
    Write-Host "Criando ambiente virtual (venv)..."
    python -m venv venv
}

# 2. Instalar dependências
Write-Host "Instalando dependências..."
.\venv\Scripts\pip install -r requirements.txt

# 3. Inicializar Banco de Dados
Write-Host "Inicializando banco de dados (SQLite)..."
.\venv\Scripts\python -m alembic upgrade head

# 4. Criar dados iniciais
Write-Host "Criando usuário administrador inicial..."
.\venv\Scripts\python app/initial_data.py

# 5. Iniciar Aplicação
Write-Host "Iniciando servidor em http://localhost:8000" -ForegroundColor Green
.\venv\Scripts\uvicorn app.main:app --reload
