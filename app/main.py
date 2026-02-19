# SISCONT - Deploy V38 (EXHAUSTION AUDIT) - 19/02/2026 19:20
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="SisCont", lifespan=lifespan)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

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
            # 1. LIST EVERY TABLE
            all_tables = conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'")).fetchall()
            
            # 2. CHECK COUNTS FOR EVERYTHING
            counts = {}
            for t in [row[0] for row in all_tables]:
                try: res = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).fetchone(); counts[t] = res[0]
                except: counts[t] = "ERR"
            
            # 3. Check for the "Venda #1" content
            venda_sample = conn.execute(text("SELECT * FROM vendas LIMIT 5")).fetchall()
            
            return {
                "all_tables_found": [row[0] for row in all_tables],
                "all_counts": counts,
                "venda_sample": [str(v) for v in venda_sample]
            }
    except Exception as e: return {"error": str(e)}
