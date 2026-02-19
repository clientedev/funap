# SISCONT - Deploy V5 (Safe Migration) - 19/02/2026 14:05
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto


def run_enum_migration():
    """Migra enums do PostgreSQL de forma segura e não destrutiva."""
    import traceback
    from sqlalchemy import text
    from app.database import engine
    
    db_url = str(engine.url)
    if "sqlite" in db_url:
        return
    
    enums_to_check = {
        "vendastatusenum": ["em_andamento", "aguardando_proposta", "aguardando_empenho", "faturado", "finalizada", "cancelada"],
        "modalidadeenum": ["venda", "licitacao", "producao"],
        "propostastatusenum": ["pendente", "aprovada", "cancelada"],
        "contratostatusenum": ["ativo", "encerrado", "cancelado"],
        "empenhostatusenum": ["pendente", "emitido", "cancelado"],
        "pedidostatusenum": ["pendente", "finalizado"],
        "nfestatusentregaenum": ["pendente", "parcial", "total"],
        "solicitacaocustostatusenum": ["pendente", "aprovada", "recusada"],
        "perfilenum": ["administrador", "consulta", "comercial", "financeiro"]
    }
    
    try:
        with engine.connect() as conn:
            # 1. Garantir que os TIPOS existem e têm todos os valores
            for type_name, labels in enums_to_check.items():
                try:
                    # Verifica se o tipo existe
                    res = conn.execute(text(f"SELECT 1 FROM pg_type WHERE typname = '{type_name}'")).fetchone()
                    if not res:
                        labels_str = ", ".join([f"'{l}'" for l in labels])
                        conn.execute(text(f"CREATE TYPE {type_name} AS ENUM ({labels_str});"))
                    else:
                        # Adiciona valores faltantes um por um (Não destrutivo)
                        for label in labels:
                            try:
                                conn.execute(text(f"ALTER TYPE {type_name} ADD VALUE IF NOT EXISTS '{label}';"))
                                conn.commit()
                            except Exception:
                                conn.rollback()
                    conn.commit()
                except Exception:
                    conn.rollback()

            # 2. Normalizar dados e Garantir Colunas
            # (Tabela, Coluna, Tipo, Default)
            target_cols = [
                ("vendas", "status", "vendastatusenum", "'em_andamento'"),
                ("vendas", "modalidade", "modalidadeenum", "'venda'"),
                ("propostas", "status", "propostastatusenum", "'pendente'"),
                ("contratos", "status", "contratostatusenum", "'ativo'"),
                ("empenhos", "status", "empenhostatusenum", "'pendente'"),
                ("pedidos", "status", "pedidostatusenum", "'pendente'"),
                ("notas_fiscais", "status_entrega", "nfestatusentregaenum", "'pendente'"),
                ("solicitacoes_custo", "status", "solicitacaocustostatusenum", "'pendente'"),
                ("usuarios", "perfil", "perfilenum", "'consulta'")
            ]

            for table, col, type_name, default_val in target_cols:
                try:
                    # Verifica se coluna existe
                    res = conn.execute(text(
                        f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'"
                    )).fetchone()
                    
                    if not res:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {type_name} DEFAULT {default_val};"))
                    else:
                        # Normaliza para lowercase antes de converter se necessário
                        conn.execute(text(f"UPDATE {table} SET {col} = LOWER({col}::TEXT) WHERE {col} IS NOT NULL;"))
                        # Garante o TYPE (Caso esteja como TEXT ou similar)
                        conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE {type_name} USING {col}::{type_name};"))
                    conn.commit()
                except Exception:
                    conn.rollback()

            # 3. REPARO EXTRA: Colunas críticas faltantes
            try:
                extra_cols = [
                    ("vendas", "processo_sei", "VARCHAR(50)"),
                    ("vendas", "objeto", "TEXT"),
                    ("vendas", "valor_total", "NUMERIC(15,2)"),
                    ("propostas", "data_emissao", "DATE"),
                    ("propostas", "data_vencimento", "DATE"),
                    ("propostas", "valor", "NUMERIC(15,2)"),
                    ("propostas", "numero", "VARCHAR(50)"),
                    ("propostas", "revisao", "VARCHAR(20)")
                ]
                for table, col, col_type in extra_cols:
                    res = conn.execute(text(
                        f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'"
                    )).fetchone()
                    if not res:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};"))
                conn.commit()
            except Exception:
                conn.rollback()
    except Exception:
        print("Erro na migração segura de enums:")
        traceback.print_exc()

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
