# SisCont - Sistema de Controle de Vendas, Licitação e Produção

Aplicação corporativa para gestão de processos de venda, licitação e produção, com controle por diretoria e perfis de acesso.

## Tecnologias
- **Backend:** Python 3.11 + FastAPI
- **Banco de Dados:** PostgreSQL 15
- **ORM:** SQLAlchemy 2.0 + Alembic (Migrations)
- **Frontend:** Jinja2 Templates + Bootstrap 5 + Chart.js
- **Infraestrutura:** Docker & docker-compose

## Como Executar

### Pré-requisitos
- Docker e Docker Compose instalados.

### Passos
1. Clone o repositório ou copie os arquivos.
2. Crie um arquivo `.env` baseado no `.env.example`:
   ```bash
   cp .env.example .env
   ```
3. Suba o ambiente com Docker:
   ```bash
   docker-compose up --build -d
   ```
4. O sistema estará disponível em `http://localhost:8000`.

### Acesso Inicial
- **Login:** admin@siscont.com
- **Senha:** admin123

## Estrutura do Projeto
- `app/models`: Definição das 11 entidades e relacionamentos.
- `app/repositories`: Camada de acesso ao banco com filtros dinâmicos.
- `app/services`: Lógica de exportação para Excel e indicadores de dashboard.
- `app/templates`: Telas HTML personalizadas.
- `alembic`: Controle de versão do banco de dados.

## Funcionalidades Principais
- Autenticação segura com JWT e hashing bcrypt.
- Controle de permissões: Usuários visualizam tudo, mas editam apenas o que pertence à sua diretoria.
- Dashboard com indicadores de vendas e propostas.
- Exportação de relatórios em formato Excel (.xlsx).
- Atualização automática do status da venda ao finalizar entrega na Nota Fiscal.
