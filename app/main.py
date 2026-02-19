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
        "UPDATE vendas SET status = 'EM ANDAMENTO' WHERE status IN ('ABERTA', 'aberta', 'PROPOSTA EM ANÁLISE', 'EMPENHADO', 'PEDIDO EMITIDO');",
        "UPDATE vendas SET status = 'FINALIZADA' WHERE status IN ('finalizada', 'FINALIZADA');",
        "UPDATE vendas SET status = 'CANCELADA' WHERE status IN ('cancelada', 'CANCELADA');",
        "UPDATE vendas SET status = 'AGUARDANDO PROPOSTA' WHERE status = 'AGUARDANDO PROPOSTA';",
        "UPDATE vendas SET status = 'AGUARDANDO EMPENHO' WHERE status = 'AGUARDANDO EMPENHO';",
        "UPDATE vendas SET status = 'FATURADO' WHERE status = 'FATURADO';",
        # Garantir que qualquer valor desconhecido vire EM ANDAMENTO
        "UPDATE vendas SET status = 'EM ANDAMENTO' WHERE status NOT IN ('EM ANDAMENTO', 'AGUARDANDO PROPOSTA', 'AGUARDANDO EMPENHO', 'FATURADO', 'FINALIZADA', 'CANCELADA');",
        "DROP TYPE IF EXISTS vendastatusenum;",
        "CREATE TYPE vendastatusenum AS ENUM ('EM ANDAMENTO', 'AGUARDANDO PROPOSTA', 'AGUARDANDO EMPENHO', 'FATURADO', 'FINALIZADA', 'CANCELADA');",
        "ALTER TABLE vendas ALTER COLUMN status TYPE vendastatusenum USING status::vendastatusenum;",
        "ALTER TABLE vendas ALTER COLUMN status SET DEFAULT 'EM ANDAMENTO';",
        # === PropostaStatusEnum ===
        "ALTER TABLE propostas ALTER COLUMN status TYPE TEXT;",
        "UPDATE propostas SET status = UPPER(status) WHERE status != UPPER(status);",
        "UPDATE propostas SET status = 'PENDENTE' WHERE status NOT IN ('PENDENTE', 'APROVADA', 'CANCELADA');",
        "DROP TYPE IF EXISTS propostastatusenum;",
        "CREATE TYPE propostastatusenum AS ENUM ('PENDENTE', 'APROVADA', 'CANCELADA');",
        "ALTER TABLE propostas ALTER COLUMN status TYPE propostastatusenum USING status::propostastatusenum;",
        "ALTER TABLE propostas ALTER COLUMN status SET DEFAULT 'PENDENTE';",
        # === ContratoStatusEnum ===
        "ALTER TABLE contratos ALTER COLUMN status TYPE TEXT;",
        "UPDATE contratos SET status = UPPER(status) WHERE status != UPPER(status);",
        "UPDATE contratos SET status = 'ATIVO' WHERE status NOT IN ('ATIVO', 'ENCERRADO', 'CANCELADO');",
        "DROP TYPE IF EXISTS contratostatusenum;",
        "CREATE TYPE contratostatusenum AS ENUM ('ATIVO', 'ENCERRADO', 'CANCELADO');",
        "ALTER TABLE contratos ALTER COLUMN status TYPE contratostatusenum USING status::contratostatusenum;",
        "ALTER TABLE contratos ALTER COLUMN status SET DEFAULT 'ATIVO';",
        # === EmpenhoStatusEnum ===
        "ALTER TABLE empenhos ALTER COLUMN status TYPE TEXT;",
        "UPDATE empenhos SET status = UPPER(status) WHERE status != UPPER(status);",
        "UPDATE empenhos SET status = 'PENDENTE' WHERE status NOT IN ('PENDENTE', 'EMITIDO', 'CANCELADO');",
        "DROP TYPE IF EXISTS empenhostatusenum;",
        "CREATE TYPE empenhostatusenum AS ENUM ('PENDENTE', 'EMITIDO', 'CANCELADO');",
        "ALTER TABLE empenhos ALTER COLUMN status TYPE empenhostatusenum USING status::empenhostatusenum;",
        "ALTER TABLE empenhos ALTER COLUMN status SET DEFAULT 'PENDENTE';",
        # === PedidoStatusEnum ===
        "ALTER TABLE pedidos ALTER COLUMN status TYPE TEXT;",
        "UPDATE pedidos SET status = UPPER(status) WHERE status != UPPER(status);",
        "UPDATE pedidos SET status = 'PENDENTE' WHERE status NOT IN ('PENDENTE', 'FINALIZADO');",
        "DROP TYPE IF EXISTS pedidostatusenum;",
        "CREATE TYPE pedidostatusenum AS ENUM ('PENDENTE', 'FINALIZADO');",
        "ALTER TABLE pedidos ALTER COLUMN status TYPE pedidostatusenum USING status::pedidostatusenum;",
        "ALTER TABLE pedidos ALTER COLUMN status SET DEFAULT 'PENDENTE';",
        # === NFEStatusEntregaEnum ===
        "ALTER TABLE notas_fiscais ALTER COLUMN status_entrega TYPE TEXT;",
        "UPDATE notas_fiscais SET status_entrega = UPPER(status_entrega) WHERE status_entrega != UPPER(status_entrega);",
        "UPDATE notas_fiscais SET status_entrega = 'PENDENTE' WHERE status_entrega NOT IN ('PENDENTE', 'ENTREGA PARCIAL', 'ENTREGA TOTAL');",
        "DROP TYPE IF EXISTS nfestatusentregaenum;",
        "CREATE TYPE nfestatusentregaenum AS ENUM ('PENDENTE', 'ENTREGA PARCIAL', 'ENTREGA TOTAL');",
        "ALTER TABLE notas_fiscais ALTER COLUMN status_entrega TYPE nfestatusentregaenum USING status_entrega::nfestatusentregaenum;",
        "ALTER TABLE notas_fiscais ALTER COLUMN status_entrega SET DEFAULT 'PENDENTE';",
        # === SolicitacaoCustoStatusEnum ===
        "ALTER TABLE solicitacoes_custo ALTER COLUMN status TYPE TEXT;",
        "UPDATE solicitacoes_custo SET status = UPPER(status) WHERE status != UPPER(status);",
        "UPDATE solicitacoes_custo SET status = 'PENDENTE' WHERE status NOT IN ('PENDENTE', 'APROVADA', 'RECUSADA');",
        "DROP TYPE IF EXISTS solicitacaocustostatusenum;",
        "CREATE TYPE solicitacaocustostatusenum AS ENUM ('PENDENTE', 'APROVADA', 'RECUSADA');",
        "ALTER TABLE solicitacoes_custo ALTER COLUMN status TYPE solicitacaocustostatusenum USING status::solicitacaocustostatusenum;",
        "ALTER TABLE solicitacoes_custo ALTER COLUMN status SET DEFAULT 'PENDENTE';",
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
