# SISCONT - Deploy V31 (SURGICAL CLEANUP) - 19/02/2026 16:55
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto

def execute_surgical_cleanup():
    """Remove defaults corrompidos que referenciam o OID fantasma 21978."""
    from sqlalchemy import text
    from app.database import engine
    if "sqlite" in str(engine.url): return
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print("V31 SURGERY: Dropping corrupted defaults...")
            # 1. Drop de defaults perigosos
            conn.execute(text('ALTER TABLE "vendas" ALTER COLUMN "status_v19" DROP DEFAULT'))
            conn.execute(text('ALTER TABLE "vendas" ALTER COLUMN "modalidade_v19" DROP DEFAULT'))
            conn.execute(text('ALTER TABLE "usuarios" ALTER COLUMN "perfil_v19" DROP DEFAULT'))
            
            # 2. Set de defaults limpos (String Literals)
            conn.execute(text("ALTER TABLE \"vendas\" ALTER COLUMN \"status_v19\" SET DEFAULT 'em_andamento'"))
            conn.execute(text("ALTER TABLE \"vendas\" ALTER COLUMN \"modalidade_v19\" SET DEFAULT 'venda'"))
            conn.execute(text("ALTER TABLE \"usuarios\" ALTER COLUMN \"perfil_v19\" SET DEFAULT 'usuario'"))
            
            # 3. Purga final
            conn.execute(text("DISCARD ALL;"))
            conn.execute(text("DEALLOCATE ALL;"))
            print("V31 SURGERY: SUCCESS. Defaults replaced with safe literals. ✅")
    except Exception as e:
        print(f"V31 SURGERY ERROR: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    execute_surgical_cleanup()
    yield

app = FastAPI(title="SisCont", version="1.0.0", lifespan=lifespan)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    return JSONResponse(status_code=500, content={"detail": str(exc), "trace": traceback.format_exc()})

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(diretorias.router)
app.include_router(usuarios.router)
app.include_router(vendas.router)
app.include_router(clientes.router)
app.include_router(linhas_produto.router)

@app.get("/seed-database")
async def seed_database():
    from app.seed_test_data import seed_data
    try:
        seed_data()
        return {"status": "Database Seeded Successfully"}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}

@app.get("/debug-db-schema")
async def debug_db_schema():
    from sqlalchemy import text, inspect
    from app.database import engine
    try:
        with engine.connect() as conn:
            oid = conn.execute(text("SELECT typname FROM pg_type WHERE oid = 21978")).fetchone()
            tables = inspect(engine).get_table_names()
            return {"oid": oid[0] if oid else "NOT FOUND", "tables": tables}
    except Exception as e: return {"error": str(e)}
