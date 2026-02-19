# SISCONT - Deploy V32 (GLOBAL forensic) - 19/02/2026 17:10
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
            
            # 1. Identificar TODAS as relações que dependem do ghost
            deps = conn.execute(text(f"""
                SELECT 
                    c.relname as table_name,
                    a.attname as column_name,
                    d.objsubid as column_num,
                    d.classid::regclass as class,
                    d.deptype
                FROM pg_depend d
                LEFT JOIN pg_class c ON d.objid = c.oid
                LEFT JOIN pg_attribute a ON d.objid = a.attrelid AND d.objsubid = a.attnum
                WHERE d.refobjid = {GHOST_OID} OR d.objid = {GHOST_OID};
            """)).fetchall()
            
            # 2. Verificar pg_type pra ver se algum OUTRO tipo tem dependência
            type_deps = conn.execute(text(f"""
                SELECT typname, oid FROM pg_type WHERE oid IN (
                    SELECT objid FROM pg_depend WHERE refobjid = {GHOST_OID}
                );
            """)).fetchall()

            return {
                "ghost_oid": GHOST_OID,
                "all_dependencies": [
                    {"table": d[0], "column": d[1], "col_num": d[2], "class": str(d[3]), "type": d[4]} 
                    for d in deps
                ],
                "dependent_types": [{"name": t[0], "oid": t[1]} for t in type_deps]
            }
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}
