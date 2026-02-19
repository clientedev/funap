# SISCONT - Deploy V35 (ECOSYSTEM HEALING) - 19/02/2026 18:25
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
            columns = conn.execute(text("SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name IN ('vendas', 'solicitacoes_custo', 'propostas')")).fetchall()
            return {"tables": tables, "columns": [str(c) for c in columns]}
    except Exception as e: return {"error": str(e)}

@app.get("/heal-ecosystem")
async def heal_ecosystem():
    from sqlalchemy import text
    from app.database import engine
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # 1. Reset sequences for reconstructed tables
            conn.execute(text("SELECT setval('usuarios_id_seq', (SELECT MAX(id) FROM usuarios))"))
            conn.execute(text("SELECT setval('vendas_id_seq', (SELECT MAX(id) FROM vendas))"))
            
            # 2. Re-establish Foreign Keys (The Absolute Eradication CASCADE dropped them)
            # Solicitacoes de Custo
            conn.execute(text('ALTER TABLE solicitacoes_custo DROP CONSTRAINT IF EXISTS solicitacoes_custo_venda_id_fkey'))
            conn.execute(text('ALTER TABLE solicitacoes_custo ADD CONSTRAINT solicitacoes_custo_venda_id_fkey FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE'))
            
            # Propostas
            conn.execute(text('ALTER TABLE propostas DROP CONSTRAINT IF EXISTS propostas_venda_id_fkey'))
            conn.execute(text('ALTER TABLE propostas ADD CONSTRAINT propostas_venda_id_fkey FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE'))

            # Contratos
            conn.execute(text('ALTER TABLE contratos DROP CONSTRAINT IF EXISTS contratos_venda_id_fkey'))
            conn.execute(text('ALTER TABLE contratos ADD CONSTRAINT contratos_venda_id_fkey FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE'))

            # Empenhos
            conn.execute(text('ALTER TABLE empenhos DROP CONSTRAINT IF EXISTS empenhos_venda_id_fkey'))
            conn.execute(text('ALTER TABLE empenhos ADD CONSTRAINT empenhos_venda_id_fkey FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE'))

            # Pedidos
            conn.execute(text('ALTER TABLE pedidos DROP CONSTRAINT IF EXISTS pedidos_venda_id_fkey'))
            conn.execute(text('ALTER TABLE pedidos ADD CONSTRAINT pedidos_venda_id_fkey FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE'))

            # Notas Fiscais
            conn.execute(text('ALTER TABLE notas_fiscais DROP CONSTRAINT IF EXISTS notas_fiscais_venda_id_fkey'))
            conn.execute(text('ALTER TABLE notas_fiscais ADD CONSTRAINT notas_fiscais_venda_id_fkey FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE'))

            return {"status": "Ecosystem Healed Successfully"}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}
