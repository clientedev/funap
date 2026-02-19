# SISCONT - Deploy V23 (EMERGENCY RESTORE) - 19/02/2026 17:15
import os
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto

def execute_recovery():
    """Tenta restaurar as tabelas sem quebrar o startup do app."""
    from sqlalchemy import text, inspect
    from app.database import engine, Base
    if "sqlite" in str(engine.url): return "Skipped (SQLite)"
    results = []
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            results.append(f"Tables found: {tables}")
            
            # Tabelas críticas para o app rodar
            core_tables = [
                'usuarios', 'vendas', 'propostas', 'contratos', 
                'empenhos', 'pedidos', 'notas_fiscais', 'solicitacoes_custo', 'diretorias', 'clientes', 'linhas_produto'
            ]
            
            for table in core_tables:
                # Tenta vários sufixos que eu possa ter usado em builds falhos
                for suffix in ["_v21_bak", "_dead_oid", "_poisoned_oid"]:
                    bak_name = f"{table}{suffix}"
                    if bak_name in tables and table not in tables:
                        results.append(f"RECOVERY: Restoring {table} from {bak_name}...")
                        conn.execute(text(f'ALTER TABLE "{bak_name}" RENAME TO "{table}"'))
                        tables.append(table)
                        break
            
            # Garante que o schema básico existe
            Base.metadata.create_all(engine)
            results.append("Base.metadata.create_all ran.")
            return "\n".join(results)
    except Exception:
        err = traceback.format_exc()
        return f"RECOVERY FAILED:\n{err}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Executa recovery mas não deixa travar o app
    try: execute_recovery()
    except: pass
    yield

app = FastAPI(title="SisCont", version="1.0.0", lifespan=lifespan)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    return JSONResponse(status_code=500, content={"detail": str(exc), "trace": traceback.format_exc()})

# CORREÇÃO: mount não é um decorator
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Rotas
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(diretorias.router)
app.include_router(usuarios.router)
app.include_router(vendas.router)
app.include_router(clientes.router)
app.include_router(linhas_produto.router)

@app.get("/panic-recovery")
async def panic_recovery():
    res = execute_recovery()
    return {"status": "Panic Recovery Executed", "details": res}

@app.get("/debug-db-schema")
async def debug_db_schema():
    from sqlalchemy import text, inspect
    from app.database import engine
    try:
        with engine.connect() as conn:
            oid_check = conn.execute(text("SELECT typname FROM pg_type WHERE oid = 21978")).fetchone()
            tables = inspect(engine).get_table_names()
            return {
                "oid_21978": oid_check[0] if oid_check else "NOT FOUND", 
                "tables": tables,
                "status": "V23 RESTORED"
            }
    except Exception as e: return {"error": str(e)}
