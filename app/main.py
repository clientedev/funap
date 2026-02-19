from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto


def run_enum_migration():
    """Migra enums do PostgreSQL de forma segura, reparando colunas se necessário."""
    import traceback
    from sqlalchemy import text
    from app.database import engine
    
    db_url = str(engine.url)
    if "sqlite" in db_url:
        return  # SQLite não tem enums nativos
    
    # Lista de tabelas e colunas que devem existir
    target_columns = [
        ("vendas", "status", "vendastatusenum", "'em_andamento'"),
        ("vendas", "modalidade", "modalidadeenum", "'venda'"),
        ("propostas", "status", "propostastatusenum", "'pendente'"),
        ("contratos", "status", "contratostatusenum", "'ativo'"),
        ("empenhos", "status", "empenhostatusenum", "'pendente'"),
        ("pedidos", "status", "pedidostatusenum", "'pendente'"),
        ("notas_fiscais", "status_entrega", "nfestatusentregaenum", "'pendente'"),
        ("solicitacoes_custo", "status", "solicitacaocustostatusenum", "'pendente'"),
    ]
    
    enums_to_recreate = {
        "vendastatusenum": ["em_andamento", "aguardando_proposta", "aguardando_empenho", "faturado", "finalizada", "cancelada"],
        "modalidadeenum": ["venda", "licitacao", "producao"],
        "propostastatusenum": ["pendente", "aprovada", "cancelada"],
        "contratostatusenum": ["ativo", "encerrado", "cancelado"],
        "empenhostatusenum": ["pendente", "emitido", "cancelado"],
        "pedidostatusenum": ["pendente", "finalizado"],
        "nfestatusentregaenum": ["pendente", "parcial", "total"],
        "solicitacaocustostatusenum": ["pendente", "aprovada", "recusada"],
    }
    
    try:
        with engine.connect() as conn:
            # 1. Remover DEFAULTS e converter para TEXT para tentar evitar o CASCADE no DROP TYPE
            for table, col, _, _ in target_columns:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} DROP DEFAULT;"))
                    conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE TEXT USING {col}::TEXT;"))
                    conn.commit()
                except Exception:
                    conn.rollback()
            
            # 2. Dropar e Recriar os Tipos ENUM
            for type_name, labels in enums_to_recreate.items():
                labels_str = ", ".join([f"'{l}'" for l in labels])
                try:
                    conn.execute(text(f"DROP TYPE IF EXISTS {type_name} CASCADE;"))
                    conn.execute(text(f"CREATE TYPE {type_name} AS ENUM ({labels_str});"))
                    conn.commit()
                except Exception:
                    conn.rollback()
            
            # 3. GARANTIR que as colunas existem (caso o CASCADE tenha dropado elas apesar da conversão para TEXT)
            for table, col, _, default_val in target_columns:
                try:
                    # Verifica se a coluna existe no schema público
                    res = conn.execute(text(
                        f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'"
                    )).fetchone()
                    
                    if not res:
                        print(f"[REPAIR] Coluna {table}.{col} não existe após o reset de enums. Recriando como TEXT...")
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} TEXT DEFAULT {default_val};"))
                        conn.commit()
                except Exception:
                    conn.rollback()

            # 4. Normalizar os dados (garantir que estão nos labels permitidos e em minúsculo)
            # Focamos na normalização de tabelas principais
            normalization_queries = [
                "UPDATE vendas SET status = 'em_andamento' WHERE status IS NULL OR UPPER(status) NOT IN ('EM_ANDAMENTO', 'AGUARDANDO_PROPOSTA', 'AGUARDANDO_EMPENHO', 'FATURADO', 'FINALIZADA', 'CANCELADA', 'EM ANDAMENTO', 'AGUARDANDO PROPOSTA', 'AGUARDANDO EMPENHO');",
                "UPDATE vendas SET status = 'em_andamento' WHERE status = 'em andando' OR status = 'em andamento';",
                "UPDATE vendas SET status = LOWER(status) WHERE status IS NOT NULL;",
                "UPDATE notas_fiscais SET status_entrega = 'parcial' WHERE UPPER(status_entrega) IN ('ENTREGA PARCIAL', 'PARCIAL');",
                "UPDATE notas_fiscais SET status_entrega = 'total' WHERE UPPER(status_entrega) IN ('ENTREGA TOTAL', 'TOTAL');",
                "UPDATE notas_fiscais SET status_entrega = 'pendente' WHERE status_entrega NOT IN ('pendente', 'parcial', 'total');"
            ]
            
            for query in normalization_queries:
                try:
                    conn.execute(text(query))
                    conn.commit()
                except Exception:
                    conn.rollback()

            # Normalização genérica para o restante
            for table, col, _, _ in target_columns:
                try:
                    conn.execute(text(f"UPDATE {table} SET {col} = LOWER({col}) WHERE {col} IS NOT NULL;"))
                    conn.commit()
                except Exception:
                    conn.rollback()

            # 5. Converter de volta para os tipos ENUM e restaurar DEFAULTS
            for table, col, type_name, default_val in target_columns:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE {type_name} USING {col}::{type_name};"))
                    conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} SET DEFAULT {default_val};"))
                    conn.commit()
                except Exception:
                    conn.rollback()

            # 6. Atualizar PerfilEnum
            try:
                conn.execute(text("ALTER TYPE perfilenum ADD VALUE IF NOT EXISTS 'comercial';"))
                conn.execute(text("ALTER TYPE perfilenum ADD VALUE IF NOT EXISTS 'financeiro';"))
                conn.commit()
            except Exception:
                conn.rollback()
    except Exception:
        print("Erro crítico na migração de enums:")
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
