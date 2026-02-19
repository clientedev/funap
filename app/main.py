# SISCONT - Deploy V7 (Deep Reset) - 19/02/2026 14:15
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto


def run_enum_migration():
    """Migra enums do PostgreSQL de forma segura usando nomes V4 para evitar cache lookup failures de OIDs antigos."""
    import traceback
    from sqlalchemy import text
    from app.database import engine
    
    db_url = str(engine.url)
    if "sqlite" in db_url:
        return
    
    # Names with _v4 suffix to guarantee fresh OIDs
    enums_to_check = {
        "vendastatusenum_v4": ["em_andamento", "aguardando_proposta", "aguardando_empenho", "faturado", "finalizada", "cancelada"],
        "modalidadeenum_v4": ["venda", "licitacao", "producao"],
        "propostastatusenum_v4": ["pendente", "aprovada", "cancelada"],
        "contratostatusenum_v4": ["ativo", "encerrado", "cancelado"],
        "empenhostatusenum_v4": ["pendente", "emitido", "cancelado"],
        "pedidostatusenum_v4": ["pendente", "finalizado"],
        "nfestatusentregaenum_v4": ["pendente", "parcial", "total"],
        "solicitacaocustostatusenum_v4": ["pendente", "aprovada", "recusada"],
        "perfilenum_v4": ["admin", "usuario", "comercial", "financeiro"]
    }
    
    try:
        # IMPORTANTE: Usar AUTOCOMMIT para comandos de TYPE no Postgres
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # 1. Garantir que os TIPOS V4 existem
            for type_name, labels in enums_to_check.items():
                try:
                    res = conn.execute(text(f"SELECT 1 FROM pg_type WHERE typname = '{type_name}'")).fetchone()
                    if not res:
                        labels_str = ", ".join([f"'{l}'" for l in labels])
                        conn.execute(text(f"CREATE TYPE {type_name} AS ENUM ({labels_str});"))
                    else:
                        for label in labels:
                            try:
                                conn.execute(text(f"ALTER TYPE {type_name} ADD VALUE IF NOT EXISTS '{label}';"))
                            except Exception:
                                pass
                except Exception:
                    print(f"Erro ao processar tipo {type_name}")

            # 2. Normalizar e Reparar Colunas (mapeando para os novos tipos _v4)
            target_cols = [
                ("vendas", "status", "vendastatusenum_v4", "'em_andamento'"),
                ("vendas", "modalidade", "modalidadeenum_v4", "'venda'"),
                ("propostas", "status", "propostastatusenum_v4", "'pendente'"),
                ("contratos", "status", "contratostatusenum_v4", "'ativo'"),
                ("empenhos", "status", "empenhostatusenum_v4", "'pendente'"),
                ("pedidos", "status", "pedidostatusenum_v4", "'pendente'"),
                ("notas_fiscais", "status_entrega", "nfestatusentregaenum_v4", "'pendente'"),
                ("solicitacoes_custo", "status", "solicitacaocustostatusenum_v4", "'pendente'"),
                ("usuarios", "perfil", "perfilenum_v4", "'usuario'")
            ]

            for table, col, type_name, default_val in target_cols:
                try:
                    # Garantir que a coluna existe
                    res = conn.execute(text(
                        f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'"
                    )).fetchone()
                    
                    if not res:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {type_name} DEFAULT {default_val};"))
                    else:
                        # Normalizar dados antes de converter
                        conn.execute(text(f"UPDATE {table} SET {col} = LOWER({col}::TEXT) WHERE {col} IS NOT NULL;"))
                        # Converter tipo para V4 de forma segura
                        conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE {type_name} USING {col}::{type_name};"))
                        conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} SET DEFAULT {default_val};"))
                except Exception as e:
                    print(f"Erro ao reparar coluna {table}.{col}: {e}")

            # 3. Colunas extras importantes
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
                try:
                    res = conn.execute(text(
                        f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'"
                    )).fetchone()
                    if not res:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};"))
                except Exception:
                    pass

            # Limpar caches para forçar recarga de metadados
            conn.execute(text("DISCARD ALL;"))
            
    except Exception:
        print("Erro na migração V4 de enums:")
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
