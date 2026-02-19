from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto


def run_enum_migration():
    """Migra enums do PostgreSQL para os novos valores na inicialização."""
    import traceback
    from sqlalchemy import text
    from app.database import engine
    
    db_url = str(engine.url)
    if "sqlite" in db_url:
        return  # SQLite não tem enums nativos
    
    migration_queries = [
        # === VendaStatusEnum ===
        "ALTER TABLE vendas ALTER COLUMN status TYPE TEXT;",
        "UPDATE vendas SET status = 'em_andamento' WHERE status IN ('ABERTA', 'aberta', 'PROPOSTA EM ANÁLISE', 'EMPENHADO', 'PEDIDO EMITIDO', 'EM ANDAMENTO');",
        "UPDATE vendas SET status = 'finalizada' WHERE status IN ('finalizada', 'FINALIZADA');",
        "UPDATE vendas SET status = 'cancelada' WHERE status IN ('cancelada', 'CANCELADA');",
        "UPDATE vendas SET status = 'aguardando_proposta' WHERE status IN ('aguardando_proposta', 'AGUARDANDO PROPOSTA');",
        "UPDATE vendas SET status = 'aguardando_empenho' WHERE status IN ('aguardando_empenho', 'AGUARDANDO EMPENHO');",
        "UPDATE vendas SET status = 'faturado' WHERE status IN ('faturado', 'FATURADO');",
        # Garantir que qualquer valor desconhecido vire em_andamento
        "UPDATE vendas SET status = 'em_andamento' WHERE status NOT IN ('em_andamento', 'aguardando_proposta', 'aguardando_empenho', 'faturado', 'finalizada', 'cancelada');",
        "DROP TYPE IF EXISTS vendastatusenum;",
        "CREATE TYPE vendastatusenum AS ENUM ('em_andamento', 'aguardando_proposta', 'aguardando_empenho', 'faturado', 'finalizada', 'cancelada');",
        "ALTER TABLE vendas ALTER COLUMN status TYPE vendastatusenum USING status::vendastatusenum;",
        "ALTER TABLE vendas ALTER COLUMN status SET DEFAULT 'em_andamento';",
        # === PropostaStatusEnum ===
        "ALTER TABLE propostas ALTER COLUMN status TYPE TEXT;",
        "UPDATE propostas SET status = LOWER(status) WHERE status != LOWER(status);",
        "UPDATE propostas SET status = 'pendente' WHERE status NOT IN ('pendente', 'aprovada', 'cancelada');",
        "DROP TYPE IF EXISTS propostastatusenum;",
        "CREATE TYPE propostastatusenum AS ENUM ('pendente', 'aprovada', 'cancelada');",
        "ALTER TABLE propostas ALTER COLUMN status TYPE propostastatusenum USING status::propostastatusenum;",
        "ALTER TABLE propostas ALTER COLUMN status SET DEFAULT 'pendente';",
        # === ContratoStatusEnum ===
        "ALTER TABLE contratos ALTER COLUMN status TYPE TEXT;",
        "UPDATE contratos SET status = LOWER(status) WHERE status != LOWER(status);",
        "UPDATE contratos SET status = 'ativo' WHERE status NOT IN ('ativo', 'encerrado', 'cancelado');",
        "DROP TYPE IF EXISTS contratostatusenum;",
        "CREATE TYPE contratostatusenum AS ENUM ('ativo', 'encerrado', 'cancelado');",
        "ALTER TABLE contratos ALTER COLUMN status TYPE contratostatusenum USING status::contratostatusenum;",
        "ALTER TABLE contratos ALTER COLUMN status SET DEFAULT 'ativo';",
        # === EmpenhoStatusEnum ===
        "ALTER TABLE empenhos ALTER COLUMN status TYPE TEXT;",
        "UPDATE empenhos SET status = LOWER(status) WHERE status != LOWER(status);",
        "UPDATE empenhos SET status = 'pendente' WHERE status NOT IN ('pendente', 'emitido', 'cancelado');",
        "DROP TYPE IF EXISTS empenhostatusenum;",
        "CREATE TYPE empenhostatusenum AS ENUM ('pendente', 'emitido', 'cancelado');",
        "ALTER TABLE empenhos ALTER COLUMN status TYPE empenhostatusenum USING status::empenhostatusenum;",
        "ALTER TABLE empenhos ALTER COLUMN status SET DEFAULT 'pendente';",
        # === PedidoStatusEnum ===
        "ALTER TABLE pedidos ALTER COLUMN status TYPE TEXT;",
        "UPDATE pedidos SET status = LOWER(status) WHERE status != LOWER(status);",
        "UPDATE pedidos SET status = 'pendente' WHERE status NOT IN ('pendente', 'finalizado');",
        "DROP TYPE IF EXISTS pedidostatusenum;",
        "CREATE TYPE pedidostatusenum AS ENUM ('pendente', 'finalizado');",
        "ALTER TABLE pedidos ALTER COLUMN status TYPE pedidostatusenum USING status::pedidostatusenum;",
        "ALTER TABLE pedidos ALTER COLUMN status SET DEFAULT 'pendente';",
        # === NFEStatusEntregaEnum ===
        "ALTER TABLE notas_fiscais ALTER COLUMN status_entrega TYPE TEXT;",
        "UPDATE notas_fiscais SET status_entrega = LOWER(status_entrega) WHERE status_entrega != LOWER(status_entrega);",
        "UPDATE notas_fiscais SET status_entrega = 'pendente' WHERE status_entrega NOT IN ('pendente', 'entrega parcial', 'entrega total');",
        "DROP TYPE IF EXISTS nfestatusentregaenum;",
        "CREATE TYPE nfestatusentregaenum AS ENUM ('pendente', 'entrega parcial', 'entrega total');",
        "ALTER TABLE notas_fiscais ALTER COLUMN status_entrega TYPE nfestatusentregaenum USING status_entrega::nfestatusentregaenum;",
        "ALTER TABLE notas_fiscais ALTER COLUMN status_entrega SET DEFAULT 'pendente';",
        # === SolicitacaoCustoStatusEnum ===
        "ALTER TABLE solicitacoes_custo ALTER COLUMN status TYPE TEXT;",
        "UPDATE solicitacoes_custo SET status = LOWER(status) WHERE status != LOWER(status);",
        "UPDATE solicitacoes_custo SET status = 'pendente' WHERE status NOT IN ('pendente', 'aprovada', 'recusada');",
        "DROP TYPE IF EXISTS solicitacaocustostatusenum;",
        "CREATE TYPE solicitacaocustostatusenum AS ENUM ('pendente', 'aprovada', 'recusada');",
        "ALTER TABLE solicitacoes_custo ALTER COLUMN status TYPE solicitacaocustostatusenum USING status::solicitacaocustostatusenum;",
        "ALTER TABLE solicitacoes_custo ALTER COLUMN status SET DEFAULT 'pendente';",
        # === PerfilEnum ===
        "ALTER TYPE perfilenum ADD VALUE IF NOT EXISTS 'comercial';",
        "ALTER TYPE perfilenum ADD VALUE IF NOT EXISTS 'financeiro';",
    ]
    
    try:
        with engine.connect() as conn:
            for query in migration_queries:
                try:
                    conn.execute(text(query))
                    conn.commit()
                except Exception:
                    conn.rollback()
        print("[MIGRATION] Enum migration completed.")
    except Exception as e:
        print(f"[MIGRATION ERROR] {traceback.format_exc()}")


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
    if exc.status_code == 403:
        return RedirectResponse(url="/dashboard")
    # Para outros erros (404, 500, etc), mostrar o erro real
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"[ERROR 500] {request.url}: {traceback.format_exc()}")
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": str(exc)})

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
