# SISCONT - Deploy V28 (DEEP OID AUDIT) - 19/02/2026 16:10
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto

@asynccontextmanager
async def lifespan(app: FastAPI):
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
        return {"status": "Database Seeded"}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

@app.get("/debug-db-schema")
async def debug_db_schema():
    from sqlalchemy import text, inspect
    from app.database import engine
    try:
        with engine.connect() as conn:
            # 1. Check for the ghost OID directly
            oid_check = conn.execute(text("SELECT typname FROM pg_type WHERE oid = 21978")).fetchone()
            
            # 2. Check ALL columns in Vendas and their underlying types
            vendas_types = conn.execute(text("""
                SELECT a.attname, t.typname, t.oid
                FROM pg_attribute a
                JOIN pg_type t ON a.atttypid = t.oid
                WHERE a.attrelid = 'vendas'::regclass AND a.attnum > 0;
            """)).fetchall()
            
            # 3. Check for any dependency on OID 21978
            deps = conn.execute(text("""
                SELECT * FROM pg_depend WHERE refobjid = 21978 OR objid = 21978;
            """)).fetchall()
            
            # 4. Check for indices or constraints
            constraints = conn.execute(text("""
                SELECT conname, contype FROM pg_constraint WHERE conrelid = 'vendas'::regclass;
            """)).fetchall()

            return {
                "oid_21978": oid_check[0] if oid_check else "NOT FOUND",
                "vendas_columns": [{"column": r[0], "type": r[1], "oid": r[2]} for r in vendas_types],
                "dependencies_count": len(deps),
                "constraints": [{"name": c[0], "type": c[1]} for c in constraints]
            }
    except Exception as e: return {"error": str(e)}
