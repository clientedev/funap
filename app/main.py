# SISCONT - Deploy V22 (RECOVERY & PURGE) - 19/02/2026 16:40
import os
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto

def run_db_recovery():
    """Recovery Logic: Se o Nuclear Reset falhou no meio, restaura as tabelas."""
    from sqlalchemy import text, inspect
    from app.database import engine, Base
    
    if "sqlite" in str(engine.url): return

    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            # Se a tabela principal sumiu e a backup existe, reverte
            core_tables = ['vendas', 'usuarios', 'propostas']
            for table in core_tables:
                if f"{table}_v21_bak" in tables and table not in tables:
                    print(f"RECOVERY: Restoring {table} from backup...")
                    conn.execute(text(f'ALTER TABLE "{table}_v21_bak" RENAME TO "{table}"'))
            
            # Garante que o schema básico existe
            Base.metadata.create_all(engine)
            
            # Cleanup final de OIDs legados (V19/V20 style)
            conn.execute(text("DEALLOCATE ALL;"))
            conn.execute(text("DISCARD ALL;"))
            print("RECOVERY V22 COMPLETE. ✅")
    except Exception:
        traceback.print_exc()

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_db_recovery()
    yield

app = FastAPI(title="SisCont", version="1.0.0", lifespan=lifespan)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401: return RedirectResponse(url="/login")
    if exc.status_code == 403: return RedirectResponse(url="/dashboard")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.mount("/static", StaticFiles(directory="app/static"), name="static")

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
    try:
        with engine.connect() as conn:
            oid_check = conn.execute(text("SELECT typname FROM pg_type WHERE oid = 21978")).fetchone()
            return {"oid_21978": oid_check[0] if oid_check else "NOT FOUND", "status": "V22 PHOENIX"}
    except Exception as e: return {"error": str(e)}
