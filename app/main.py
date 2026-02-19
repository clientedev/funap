from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto


def run_enum_migration():
    """Migra enums do PostgreSQL para os novos valores na inicialização."""
    from sqlalchemy import text
    from app.database import engine
    
    if engine.url.drivername.startswith("sqlite"):
        return  # SQLite não tem enums nativos
    
    migration_queries = [
        # --- VendaStatusEnum ---
        "ALTER TABLE vendas ALTER COLUMN status TYPE TEXT;",
        "UPDATE vendas SET status = 'EM ANDAMENTO' WHERE status = 'ABERTA' OR status = 'aberta';",
        "UPDATE vendas SET status = 'FINALIZADA' WHERE status = 'finalizada';",
        "UPDATE vendas SET status = 'CANCELADA' WHERE status = 'cancelada';",
        "DROP TYPE IF EXISTS vendastatusenum;",
        "CREATE TYPE vendastatusenum AS ENUM ('EM ANDAMENTO', 'AGUARDANDO PROPOSTA', 'AGUARDANDO EMPENHO', 'FATURADO', 'FINALIZADA', 'CANCELADA');",
        "ALTER TABLE vendas ALTER COLUMN status TYPE vendastatusenum USING status::vendastatusenum;",
        "ALTER TABLE vendas ALTER COLUMN status SET DEFAULT 'EM ANDAMENTO';",
        # --- ContratoStatusEnum ---
        "ALTER TABLE contratos ALTER COLUMN status TYPE TEXT;",
        "UPDATE contratos SET status = UPPER(status) WHERE status != UPPER(status);",
        "DROP TYPE IF EXISTS contratostatusenum;",
        "CREATE TYPE contratostatusenum AS ENUM ('ATIVO', 'ENCERRADO', 'CANCELADO');",
        "ALTER TABLE contratos ALTER COLUMN status TYPE contratostatusenum USING status::contratostatusenum;",
        "ALTER TABLE contratos ALTER COLUMN status SET DEFAULT 'ATIVO';",
        # --- EmpenhoStatusEnum ---
        "ALTER TABLE empenhos ALTER COLUMN status TYPE TEXT;",
        "UPDATE empenhos SET status = UPPER(status) WHERE status != UPPER(status);",
        "DROP TYPE IF EXISTS empenhostatusenum;",
        "CREATE TYPE empenhostatusenum AS ENUM ('PENDENTE', 'EMITIDO', 'CANCELADO');",
        "ALTER TABLE empenhos ALTER COLUMN status TYPE empenhostatusenum USING status::empenhostatusenum;",
        "ALTER TABLE empenhos ALTER COLUMN status SET DEFAULT 'PENDENTE';",
        # --- SolicitacaoCustoStatusEnum ---
        "ALTER TABLE solicitacoes_custo ALTER COLUMN status TYPE TEXT;",
        "UPDATE solicitacoes_custo SET status = UPPER(status) WHERE status != UPPER(status);",
        "DROP TYPE IF EXISTS solicitacaocustostatusenum;",
        "CREATE TYPE solicitacaocustostatusenum AS ENUM ('PENDENTE', 'APROVADA', 'RECUSADA');",
        "ALTER TABLE solicitacoes_custo ALTER COLUMN status TYPE solicitacaocustostatusenum USING status::solicitacaocustostatusenum;",
        "ALTER TABLE solicitacoes_custo ALTER COLUMN status SET DEFAULT 'PENDENTE';",
        # --- PerfilEnum (adicionar novos valores) ---
        "ALTER TYPE perfilenum ADD VALUE IF NOT EXISTS 'comercial';",
        "ALTER TYPE perfilenum ADD VALUE IF NOT EXISTS 'financeiro';",
    ]
    
    try:
        with engine.connect() as conn:
            for query in migration_queries:
                try:
                    conn.execute(text(query))
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    err = str(e)
                    if "already exists" in err or "DuplicateObject" in err or "does not exist" in err:
                        pass  # Ignora erros idempotentes
                    else:
                        print(f"[MIGRATION WARNING] {err[:100]}")
        print("[MIGRATION] Enum migration completed successfully.")
    except Exception as e:
        print(f"[MIGRATION ERROR] {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_enum_migration()
    yield


app = FastAPI(title="SisCont", version="1.0.0", lifespan=lifespan)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    return RedirectResponse(url="/login") 

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(diretorias.router)
app.include_router(usuarios.router)
app.include_router(vendas.router)
app.include_router(clientes.router)
app.include_router(linhas_produto.router)

@app.get("/")
def root():
    return RedirectResponse(url="/dashboard")
