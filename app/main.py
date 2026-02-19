# SISCONT - Deploy V30 (SAFE FORENSIC) - 19/02/2026 16:40
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

@app.get("/debug-db-schema")
async def debug_db_schema():
    from sqlalchemy import text
    from app.database import engine
    try:
        with engine.connect() as conn:
            GHOST_OID = 21978
            
            # 1. Dependências brutas
            deps = conn.execute(text(f"""
                SELECT classid, objid, objsubid, refclassid, refobjid, deptype
                FROM pg_depend 
                WHERE refobjid = {GHOST_OID} OR objid = {GHOST_OID};
            """)).fetchall()
            
            # 2. Defaults brutos (sem pg_get_expr que crasha)
            # Vamos buscar todas as tabelas que tem algum default suspeito
            # Como não podemos usar LIKE no binary, vamos pegar todos os defaults de 'vendas' e 'usuarios'
            vendas_defaults = conn.execute(text("""
                SELECT adrelid::regclass, adnum, adbin::text 
                FROM pg_attrdef 
                WHERE adrelid = 'vendas'::regclass OR adrelid = 'usuarios'::regclass;
            """)).fetchall()

            return {
                "ghost_oid": GHOST_OID,
                "pg_depend_raw": [{"cid": d[0], "oid": d[1], "sub": d[2], "rcid": d[3], "roid": d[4], "type": d[5]} for d in deps],
                "defaults_brutos": [{"table": str(d[0]), "col_num": d[1], "adbin_sample": d[2][:100] if d[2] else ""} for d in vendas_defaults]
            }
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}
