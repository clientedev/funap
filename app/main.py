# SISCONT - Deploy V12 (Native Enum Shutdown) - 19/02/2026 14:48
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto


def run_enum_migration():
    """Migra colunas de Enum para TEXT para resolver definitivamente o erro de cache OID lookup do Postgres."""
    import traceback
    from sqlalchemy import text
    from app.database import engine
    
    db_url = str(engine.url)
    if "sqlite" in db_url:
        return
    
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # 0. Limpar planos e caches da sessão ATUAL e definir timeouts
            conn.execute(text("DISCARD ALL;"))
            conn.execute(text("SET lock_timeout = '20s';"))
            conn.execute(text("SET statement_timeout = '40s';"))
            
            # NOVO: Tentar encerrar outras conexões para liberar locks de DDL
            try:
                conn.execute(text("""
                    SELECT pg_terminate_backend(pid) 
                    FROM pg_stat_activity 
                    WHERE datname = current_database() 
                    AND pid <> pg_backend_pid();
                """))
            except: pass

            # 1. Lista de colunas para converter para TEXT
            target_cols = [
                ("vendas", "status"),
                ("vendas", "modalidade"),
                ("propostas", "status"),
                ("contratos", "status"),
                ("empenhos", "status"),
                ("pedidos", "status"),
                ("notas_fiscais", "status_entrega"),
                ("solicitacoes_custo", "status"),
                ("usuarios", "perfil")
            ]

            print("Convertendo colunas para TEXT (Scorched Earth V12)...")
            for table, col in target_cols:
                try:
                    # Garantir que a coluna existe
                    res = conn.execute(text(
                        f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'"
                    )).fetchone()
                    
                    if res:
                        # Dropar default primeiro
                        conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} DROP DEFAULT;"))
                        # Converter para TEXT
                        conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE TEXT USING {col}::TEXT;"))
                        print(f"Repaired: {table}.{col} -> TEXT")
                except Exception as e:
                    print(f"Erro em {table}.{col}: {e}")

            # 2. ELIMINAR TODOS OS TIPOS ENUM ANTIGOS (v1, v2, v3, v4, v5, etc)
            print("Eliminando tipos Enum nativos...")
            try:
                res = conn.execute(text("SELECT typname FROM pg_type WHERE typname LIKE '%enum%'"))
                for row in res:
                    try:
                        conn.execute(text(f"DROP TYPE IF EXISTS {row[0]} CASCADE;"))
                        print(f"Dropped type: {row[0]}")
                    except: pass
            except: pass

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
                except: pass

            conn.execute(text("DISCARD ALL;"))
            print("MIGRAÇÃO V12 (TEXT CONVERSION) CONCLUÍDA. ✅")
            
    except Exception:
        print("Erro na migração V12:")
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
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"[ERROR 500] {request.url}: {traceback.format_exc()}")
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": str(exc)})

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(diretorias.router)
app.include_router(usuarios.router)
app.include_router(vendas.router)
app.include_router(clientes.router)
app.include_router(linhas_produto.router)

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
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"[ERROR 500] {request.url}: {traceback.format_exc()}")
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": str(exc)})

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(diretorias.router)
app.include_router(usuarios.router)
app.include_router(vendas.router)
app.include_router(clientes.router)
app.include_router(linhas_produto.router)
