# SISCONT - Deploy V36 (ABSOLUTE RESTORATION) - 19/02/2026 18:45
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

@app.get("/")
async def root():
    return RedirectResponse(url="/login")

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
            tables = inspect(engine).get_table_names()
            counts = {}
            for t in tables:
                try:
                    res = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).fetchone()
                    counts[t] = res[0]
                except: counts[t] = "ERROR"
            
            return {
                "tables": tables,
                "row_counts": counts,
                "database_url_host": str(engine.url).split("@")[-1] if "@" in str(engine.url) else "LOCAL"
            }
    except Exception as e: return {"error": str(e)}

@app.get("/heal-ecosystem")
async def heal_ecosystem():
    from sqlalchemy import text
    from app.database import engine
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print("V36 HEALING: Restoring Sequences and FKs...")
            # 1. Reset sequences
            conn.execute(text("SELECT setval('usuarios_id_seq', (SELECT COALESCE(MAX(id), 1) FROM usuarios))"))
            conn.execute(text("SELECT setval('vendas_id_seq', (SELECT COALESCE(MAX(id), 1) FROM vendas))"))
            
            # 2. Restore all FKs that might have been dropped by CASCADE
            tables_to_link = {
                "solicitacoes_custo": "venda_id",
                "propostas": "venda_id",
                "contratos": "venda_id",
                "empenhos": "venda_id",
                "pedidos": "venda_id",
                "notas_fiscais": "venda_id"
            }
            
            for table, col in tables_to_link.items():
                try:
                    conn.execute(text(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_{col}_fkey'))
                    conn.execute(text(f'ALTER TABLE {table} ADD CONSTRAINT {table}_{col}_fkey FOREIGN KEY ({col}) REFERENCES vendas(id) ON DELETE CASCADE'))
                    print(f"V36 HEALING: Restored FK for {table}")
                except Exception as ex:
                    print(f"V36 HEALING: Skipping FK for {table} - {ex}")

            return {"status": "Ecosystem Healed and Sequences Reset Successfully"}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}
