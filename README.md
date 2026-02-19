# 🏛️ SISCONT — Sistema de Controle de Vendas (FUNAP)

> Sistema web completo para gestão e acompanhamento do ciclo de vida de vendas institucionais da FUNAP. Controle desde a abertura de uma venda até a emissão de notas fiscais, passando por propostas, contratos, empenhos e pedidos.

---

## 📸 Visão Geral

O **SISCONT** digitaliza e centraliza todo o fluxo comercial da FUNAP, eliminando planilhas e controles manuais. Cada venda segue um pipeline claro com rastreabilidade total:

```
Abertura da Venda → DIPRO (Custo) → Proposta → Contrato → Empenho → Pedido → Nota Fiscal → Finalizada
```

---

## ✨ Funcionalidades

### 📊 Dashboard
- Painel com métricas em tempo real: total de vendas por status, valores, quantidade por diretoria.
- Visão consolidada para gestores.

### 🛒 Vendas (Módulo Principal)
O coração do sistema. Cada venda possui:

| Etapa | Descrição | Exemplo |
|:---|:---|:---|
| **Abertura** | Registro da venda com cliente, linha de produto, valor e diretoria | Venda #001 — Cliente: Prefeitura de SP, Produto: Mobiliário, Valor: R$ 50.000 |
| **DIPRO (Solicitação de Custo)** | Cálculo dos custos internos antes da proposta | Custo: R$ 32.000, Descrição: "Matéria-prima + mão de obra" |
| **Proposta** | Proposta comercial enviada ao cliente | Proposta #2024-001, Valor: R$ 50.000, Prazo: 90 dias |
| **Contrato** | Formalização do acordo com nº de contrato e vigência | Contrato CT-2024/0045, Vigência: 01/03/2024 a 01/03/2025 |
| **Empenho** | Registro do empenho orçamentário do órgão público | Empenho NE-2024-789, Valor empenhado: R$ 50.000 |
| **Pedido** | Pedido de produção/entrega com prazo | Pedido #P-001, Prazo de entrega: 30/06/2024 |
| **Nota Fiscal** | Emissão da NF com anexo de PDF/Imagem | NF 001.234, Valor: R$ 50.000, Status: Entrega Total |

**Exemplo de uso:** Ao criar uma venda, o gestor preenche os dados básicos. O sistema then acompanha o progresso por abas (DIPRO → Proposta → Contrato → etc.), mostrando o status atualizado em cada etapa.

### 👥 Clientes
- Cadastro completo de clientes (CNPJ, razão social, endereço, contato).
- **Importação em massa via Excel** — faça upload de uma planilha `.xlsx` e o sistema cadastra todos os clientes automaticamente.
- Pesquisa e filtro de clientes.

### 📦 Linhas de Produto
- Cadastro de categorias/linhas de produto: Mobiliário, Confecção, Alimentação, etc.
- Cada venda é vinculada a uma linha de produto.

### 🏢 Diretorias
- Cadastro de diretorias da FUNAP.
- Cada venda pertence a uma diretoria (controle de acesso por hierarquia).

### 👤 Usuários e Permissões
- Sistema de autenticação com JWT (token seguro, httponly cookie).
- Perfis de acesso: **Admin** e **Usuário**.
- Admin pode criar/editar usuários e configurar permissões por diretoria.

### 📎 Anexo de Documentos
- Upload de arquivos (PDF, JPG, PNG) diretamente nos modais de Nota Fiscal.
- Arquivos salvos de forma segura no servidor.

### 📱 Responsividade Mobile
- Interface 100% responsiva para smartphones e tablets.
- Menu lateral com toggle (hamburguer) e overlay em telas pequenas.
- Abas com rolagem horizontal para navegação confortável no celular.

### 📥 Exportação Excel
- Exportação de relatórios e listagens em formato `.xlsx`.

---

## 🚀 Tecnologias

| Camada | Tecnologia |
|:---|:---|
| **Backend** | Python 3.11 + FastAPI |
| **Banco de Dados** | PostgreSQL 15 + SQLAlchemy ORM |
| **Frontend** | HTML5, Jinja2, Bootstrap 5, FontAwesome |
| **Autenticação** | JWT (python-jose) + Bcrypt (passlib) |
| **Servidor Produção** | Gunicorn + Uvicorn Workers |
| **Deploy** | Railway (via Docker) |
| **Excel** | Pandas + OpenPyXL |

---

## 📂 Estrutura do Projeto

```
siscont/
├── app/
│   ├── main.py              # Ponto de entrada da aplicação FastAPI
│   ├── database.py           # Configuração do banco de dados e sessões
│   ├── auth/                 # Segurança: JWT, hashing, permissões
│   ├── models/               # Modelos SQLAlchemy (tabelas do banco)
│   │   ├── venda.py          # Vendas (modelo principal)
│   │   ├── cliente.py        # Clientes
│   │   ├── proposta.py       # Propostas comerciais
│   │   ├── contrato.py       # Contratos
│   │   ├── empenho.py        # Empenhos orçamentários
│   │   ├── pedido.py         # Pedidos de entrega
│   │   ├── nota_fiscal.py    # Notas fiscais (com anexo)
│   │   ├── solicitacao_custo.py  # DIPRO (custos)
│   │   ├── usuario.py        # Usuários do sistema
│   │   ├── diretoria.py      # Diretorias
│   │   └── linha_produto.py  # Linhas de produto
│   ├── routers/              # Rotas (controllers)
│   │   ├── vendas.py         # CRUD de vendas e sub-módulos
│   │   ├── clientes.py       # CRUD de clientes + importação Excel
│   │   ├── dashboard.py      # Dashboard de métricas
│   │   ├── auth.py           # Login/Logout
│   │   ├── usuarios.py       # CRUD de usuários
│   │   ├── diretorias.py     # CRUD de diretorias
│   │   └── linhas_produto.py # CRUD de linhas de produto
│   ├── templates/            # Páginas HTML (Jinja2)
│   ├── static/               # CSS, JS, imagens, uploads
│   └── services/             # Lógica de exportação Excel
├── alembic/                  # Migrations do banco de dados
├── Dockerfile                # Build da imagem Docker
├── docker-compose.yml        # Orquestração local (app + PostgreSQL)
├── entrypoint.sh             # Script de inicialização em produção
├── requirements.txt          # Dependências Python
├── run_local.ps1             # Script automático para rodar local (Windows)
└── .env.example              # Template de variáveis de ambiente
```

---

## 🛠️ Instalação e Execução Local

### Pré-requisitos
- **Python 3.11+** instalado
- **PostgreSQL 15+** instalado e rodando (ou use Docker)
- **Git** instalado

### Opção 1: Script Automático (Windows)

```powershell
# 1. Clone o repositório
git clone https://github.com/seu-usuario/siscont.git
cd siscont

# 2. Copie e configure o .env
cp .env.example .env
# Edite o .env com suas configurações de banco

# 3. Execute o script automático
powershell -ExecutionPolicy Bypass -File run_local.ps1
```

O script faz tudo automaticamente: cria o venv, instala dependências, roda migrations e inicia o servidor.

### Opção 2: Passo a Passo Manual

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/siscont.git
cd siscont

# 2. Crie e ative o ambiente virtual
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com seus dados:
#   DATABASE_URL=postgresql://usuario:senha@localhost:5432/siscont
#   SECRET_KEY=uma-chave-secreta-longa-e-aleatoria
#   FIRST_ADMIN_EMAIL=admin@siscont.com
#   FIRST_ADMIN_PASSWORD=admin123
#   FIRST_ADMIN_NOME=Administrador

# 5. Crie o banco de dados (no psql)
psql -U postgres -c "CREATE DATABASE siscont;"

# 6. Rode as migrations e crie dados iniciais
alembic upgrade head
python -m app.create_tables
python -m app.initial_data

# 7. Inicie o servidor
uvicorn app.main:app --reload
```

**Acesse:** http://localhost:8000

**Login padrão:** Use o email e senha definidos em `FIRST_ADMIN_EMAIL` e `FIRST_ADMIN_PASSWORD`.

### Opção 3: Docker Compose (Recomendada)

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/siscont.git
cd siscont

# 2. Configure o .env
cp .env.example .env

# 3. Suba tudo com Docker Compose
docker-compose up --build
```

Isso cria automaticamente:
- Um container **PostgreSQL 15** com persistência de dados.
- Um container **Python** com a aplicação rodando em Gunicorn.

**Acesse:** http://localhost:8000

---

## ☁️ Deploy em Produção (Railway)

O SISCONT está preparado para deploy automático via Railway + Docker.

### Passo a Passo

1. **Crie uma conta** em [railway.app](https://railway.app/).

2. **Crie um novo projeto** e conecte ao repositório GitHub.

3. **Adicione um banco PostgreSQL:**
   - No painel do Railway, clique em **"Add Service"** → **"Database"** → **"PostgreSQL"**.
   - O Railway gera automaticamente a `DATABASE_URL`.

4. **Configure as variáveis de ambiente:**
   No painel do serviço da aplicação, vá em **"Variables"** e adicione:

   | Variável | Descrição | Exemplo |
   |:---|:---|:---|
   | `DATABASE_URL` | Preenchida automaticamente pelo Railway | `postgresql://...` |
   | `SECRET_KEY` | Chave secreta para tokens JWT | `minha-chave-super-secreta-123` |
   | `FIRST_ADMIN_EMAIL` | Email do primeiro administrador | `admin@funap.sp.gov.br` |
   | `FIRST_ADMIN_PASSWORD` | Senha do primeiro administrador | `SenhaSegura@2024` |
   | `FIRST_ADMIN_NOME` | Nome do administrador | `Administrador` |

5. **Deploy automático:**
   - A cada `git push` na branch `main`, o Railway faz build e deploy automático.
   - O `entrypoint.sh` roda migrations, cria tabelas e inicia o servidor Gunicorn com 4 workers.

6. **Acesse o sistema** pela URL gerada pelo Railway (ex: `https://siscont-production.up.railway.app`).

### Fluxo de Inicialização em Produção

```
entrypoint.sh
  ├── alembic upgrade head        # Aplica migrations pendentes
  ├── python -m app.create_tables # Garante que todas as tabelas existem
  ├── python -m app.initial_data  # Cria o usuário admin (se não existir)
  └── gunicorn (4 workers)        # Inicia o servidor na porta $PORT
```

---

## 🔐 Variáveis de Ambiente

| Variável | Obrigatória | Padrão | Descrição |
|:---|:---:|:---|:---|
| `DATABASE_URL` | ✅ | — | URL de conexão PostgreSQL |
| `SECRET_KEY` | ✅ | — | Chave secreta para JWT |
| `ALGORITHM` | ❌ | `HS256` | Algoritmo de criptografia do token |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `480` | Tempo de expiração do login (minutos) |
| `FIRST_ADMIN_EMAIL` | ✅ | — | Email do admin inicial |
| `FIRST_ADMIN_PASSWORD` | ✅ | — | Senha do admin inicial |
| `FIRST_ADMIN_NOME` | ✅ | — | Nome do admin inicial |

---

## 📋 Exemplo de Fluxo Completo

```
1. Gestor faz login no sistema.
2. No Dashboard, visualiza as métricas gerais.
3. Clica em "Nova Venda" → preenche: cliente, linha de produto, valor, diretoria.
4. Na venda criada, abre a aba "DIPRO" → adiciona solicitação de custo.
5. Aba "Proposta" → registra a proposta enviada ao cliente.
6. Aba "Contrato" → registra o contrato assinado.
7. Aba "Empenho" → registra o empenho orçamentário recebido.
8. Aba "Pedido" → registra o pedido de produção.
9. Aba "Nota Fiscal" → emite a NF e anexa o PDF.
10. O status da venda é atualizado automaticamente a cada etapa!
```

---

## 🤝 Contribuição

1. Faça um fork do projeto.
2. Crie uma branch: `git checkout -b minha-feature`.
3. Commit suas alterações: `git commit -m 'feat: minha nova feature'`.
4. Push para a branch: `git push origin minha-feature`.
5. Abra um Pull Request.

---

## 📄 Licença

Este projeto é de uso interno da **FUNAP — Fundação Prof. Dr. Manoel Pedro Pimentel**.

---

© 2026 - FUNAP | Desenvolvido com ❤️ para a gestão pública
