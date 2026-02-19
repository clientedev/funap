# SISCONT - Deploy V37 (EMERGENCY AUDIT) - 19/02/2026 19:10
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
            # 1. Check counts
            tables = ["vendas", "solicitacoes_custo", "propostas", "contratos", "empenhos", "pedidos", "notas_fiscais"]
            counts = {}
            for t in tables:
                try: res = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).fetchone(); counts[t] = res[0]
                except: counts[t] = "ERROR"
            
            # 2. Check if ANY backup table exists still
            backups = conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE tablename LIKE '%%ghost%%' OR tablename LIKE '%%v19%%' OR tablename LIKE '%%v21%%'")).fetchall()
            
            # 3. Check Venda columns
            v_cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'vendas'")).fetchall()
            
            return {
                "counts": counts,
                "backup_tables": [b[0] for b in backups],
                "venda_columns": [v[0] for v in v_cols]
            }
    except Exception as e: return {"error": str(e)}
