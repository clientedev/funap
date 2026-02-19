# SISCONT - Sistema de Controle de Vendas (FUNAP)

O **SISCONT** é uma aplicação web para gestão e controle de vendas, desenvolvida especificamente para as necessidades da FUNAP. O sistema oferece módulos para gestão de clientes, linhas de produtos, vendas e relatórios (Dashboard).

## 🚀 Tecnologias Utilizadas

- **Backend:** FastAPI (Python 3.11)
- **Banco de Dados:** PostgreSQL (com SQLAlchemy ORM)
- **Frontend:** HTML5, Jinja2 Templates, Bootstrap 5, FontAwesome
- **Servidor de Produção:** Gunicorn + Uvicorn
- **Deploy:** Railway (via Docker)
- **Exportação/Importação:** Pandas e OpenPyXL (Excel)

## 📂 Estrutura do Projeto

- `/app`: Código-fonte principal da aplicação.
  - `/models`: Definições das tabelas do banco de dados.
  - `/routers`: Rotas e lógica de backend da API/Web.
  - `/templates`: Páginas HTML (Jinja2).
  - `/static`: Arquivos estáticos (CSS, JS, Imagens).
  - `/auth`: Lógica de segurança e tokens JWT.
- `/alembic`: Configurações de migração (embora o sistema use auto-create no boot).
- `entrypoint.sh`: Script de inicialização para containers/deploy.

## 🛠️ Instalação e Execução Local

1. Clone o repositório.
2. Crie um ambiente virtual: `python -m venv venv`.
3. Ative o venv e instale as dependências: `pip install -r requirements.txt`.
4. Configure o arquivo `.env` (use o `.env.example` como base).
5. Execute o sistema: `uvicorn app.main:app --reload`.

## ☁️ Deploy no Railway

O projeto está configurado para deploy automático via Docker.

### Variáveis de Ambiente Necessárias:

| Variável | Descrição |
| :--- | :--- |
| `DATABASE_URL` | URL completa do PostgreSQL (Railway preenche automático). |
| `SECRET_KEY` | Chave secreta para segurança dos tokens. |
| `FIRST_ADMIN_EMAIL` | Email do administrador principal. |
| `FIRST_ADMIN_PASSWORD` | Senha do administrador principal. |
| `FIRST_ADMIN_NOME` | Nome do administrador principal. |

### Fluxo de Inicialização:
Sempre que o projeto sobe no Railway, o script `entrypoint.sh` executa:
1. Verificação/Criação das tabelas no banco.
2. Criação ou Atualização do usuário administrador (conforme variáveis de ambiente).
3. Inicialização do servidor Gunicorn.

## 👥 Módulos do Sistema

- **Dashboard:** Visão geral de vendas e métricas.
- **Vendas:** Cadastro completo de vendas e fluxos de aprovação.
- **Clientes:** Gestão de clientes com importação via Excel.
- **Linhas de Produto:** Cadastro de categorias de produtos.
- **Usuários/Diretorias:** Controle de acesso por perfil e hierarquia organizacional.

---
© 2026 - FUNAP
