# SISCONT - Deploy V20 (CLEANUP & CASING) - 19/02/2026 16:05
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto


def run_enum_migration():
    """Remove colunas legadas corrompidas e garante a saúde do schema v19."""
    import traceback
    from sqlalchemy import text
    from app.database import engine
    
    db_url = str(engine.url)
    if "sqlite" in db_url: return

    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print("CACHE NUKE: Clearing Postgres session caches...")
            conn.execute(text("DISCARD ALL;"))
            conn.execute(text("DEALLOCATE ALL;"))
            conn.execute(text("SET lock_timeout = '50s';"))
            
            # Encerrar outras conexões
            try:
                conn.execute(text("""
                    SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
                    WHERE datname = current_database() AND pid <> pg_backend_pid();
                """))
            except: pass

            # Lista de colunas legadas para DROPAR (Dados já migrados para _v19)
            legacy_cols = [
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

            print("CLEANUP V20: Dropping legacy columns to restore creation flow...")
            for table, col in legacy_cols:
                try:
                    # Tentar dropar a coluna legado. Se falhar (já dropada), ignore.
                    print(f"   -> Dropping {table}.{col} (legacy)")
                    conn.execute(text(f'ALTER TABLE "{table}" DROP COLUMN IF EXISTS "{col}" CASCADE'))
                    print(f"      ✅ Deleted {table}.{col}")
                except Exception as e:
                    print(f"      ⚠️ Info: {table}.{col} could not be dropped or already gone: {e}")

            # Cleanup native types leftover
            print("CLEANUP: Dropping enum types...")
            try:
                res = conn.execute(text("SELECT typname FROM pg_type WHERE typname LIKE '%enum%'"))
                for row in res:
                    try:
                        conn.execute(text(f'DROP TYPE IF EXISTS "{row[0]}" CASCADE'))
                    except: pass
            except: pass

            conn.execute(text("ANALYZE;"))
            conn.execute(text("DISCARD ALL;"))
            print("MIGRAÇÃO V20 CONCLUÍDA. ✅")
            
    except Exception:
        print("Erro crítico na migração V20:")
        traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_enum_migration()
    yield


app = FastAPI(title="SisCont", version="1.0.0", lifespan=lifespan)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401: return RedirectResponse(url="/login")
    if exc.status_code == 403: return RedirectResponse(url="/dashboard")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"[ERROR 500] {request.url}: {traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": str(exc)})

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Rotas
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(diretorias.router)
app.include_router(usuarios.router)
app.include_router(vendas.router)
app.include_router(clientes.router)
app.include_router(linhas_produto.router)

@app.get("/debug-db-schema")
async def debug_db_schema():
    from sqlalchemy import text
    from app.database import engine
    target_tables = ['vendas', 'propostas', 'contratos', 'empenhos', 'pedidos', 'notas_fiscais', 'solicitacoes_custo', 'usuarios']
    try:
        with engine.connect() as conn:
            schema_res = conn.execute(text(f"""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name IN ({','.join([f"'{t}'" for t in target_tables])})
                AND (column_name LIKE '%v19%' OR column_name LIKE '%status%' OR column_name = 'perfil' OR column_name = 'modalidade')
            """)).fetchall()
            return {"columns": [{"table": r[0], "column": r[1], "type": r[2]} for r in schema_res]}
    except Exception as e: return {"error": str(e)}
