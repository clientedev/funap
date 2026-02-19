# SISCONT - Deploy V29 (FORENSIC AUDIT) - 19/02/2026 16:30
import os
import traceback
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
        return {"error": str(e), "trace": traceback.format_exc()}

@app.get("/debug-db-schema")
async def debug_db_schema():
    from sqlalchemy import text, inspect
    from app.database import engine
    try:
        with engine.connect() as conn:
            # Ghost OID
            GHOST_OID = 21978
            
            # 1. Dependências detalhadas
            deps = conn.execute(text(f"""
                SELECT 
                    classid::regclass as class, 
                    objid as object_id, 
                    objsubid as sub_id,
                    refclassid::regclass as ref_class,
                    refobjid as ref_object_id,
                    refobjsubid as ref_sub_id,
                    deptype
                FROM pg_depend 
                WHERE refobjid = {GHOST_OID} OR objid = {GHOST_OID};
            """)).fetchall()
            
            # 2. Defaults de colunas (pg_attrdef)
            defaults = conn.execute(text(f"""
                SELECT 
                    adrelid::regclass as table_name,
                    adnum as column_num,
                    pg_get_expr(adbin, adrelid) as expression
                FROM pg_attrdef
                WHERE adbin::text LIKE '%{GHOST_OID}%';
            """)).fetchall()
            
            # 3. Triggers
            triggers = conn.execute(text(f"""
                SELECT tgname, tgrelid::regclass as table_name
                FROM pg_trigger
                WHERE tgfoid IN (SELECT oid FROM pg_proc WHERE prosrc LIKE '%{GHOST_OID}%');
            """)).fetchall()

            # 4. Tipos remanescentes
            ghost_types = conn.execute(text(f"SELECT oid, typname FROM pg_type WHERE typname LIKE '%v4%' OR typname LIKE '%v5%';")).fetchall()

            return {
                "ghost_oid": GHOST_OID,
                "pg_depend": [{"class": d[0], "obj_id": d[1], "sub_id": d[2], "ref_class": d[3], "ref_obj_id": d[4], "deptype": d[6]} for d in deps],
                "pg_attrdef": [{"table": d[0], "col": d[1], "expr": d[2]} for d in defaults],
                "triggers": [{"name": t[0], "table": t[1]} for t in triggers],
                "ghost_types": [{"oid": t[0], "name": t[1]} for t in ghost_types]
            }
    except Exception as e: return {"error": str(e)}
