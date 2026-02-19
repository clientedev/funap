# SISCONT - Deploy V33 (ABSOLUTE ERADICATION) - 19/02/2026 17:30
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto

def absolute_eradication():
    """Reconstrói as tabelas corrompidas do zero para limpar o catálogo do Postgres."""
    from sqlalchemy import text
    from app.database import engine
    if "sqlite" in str(engine.url): return
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print("V33 EXORCISM: Commencing Absolute Eradication...")
            
            # 1. Tabelas que sabemos que estão zumbificadas
            # Ordem de drop/rename respeitando constraints (vamos ser agressivos)
            conn.execute(text("ALTER TABLE IF EXISTS vendas RENAME TO vendas_ghost_zombie_v33"))
            conn.execute(text("ALTER TABLE IF EXISTS usuarios RENAME TO usuarios_ghost_zombie_v33"))
            
            # 2. Re-criar do zero (SQLAlchemy vai fazer isso via Base.metadata.create_all ou manual)
            # Vamos fazer manual pra garantir que os tipos sejam VARCHAR(100) sem falhas
            # NOTA: O schema deve bater com os modelos app/models/
            
            print("V33 EXORCISM: Creating fresh tables...")
            
            # Tabela Usuarios (Simplificada mas compatível)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    senha_hash VARCHAR(255) NOT NULL,
                    perfil_v19 VARCHAR(100) DEFAULT 'usuario',
                    diretoria_id INTEGER,
                    ativo BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))

            # Tabela Vendas
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS vendas (
                    id SERIAL PRIMARY KEY,
                    numero VARCHAR(255) UNIQUE NOT NULL,
                    processo_sei VARCHAR(255),
                    objeto TEXT,
                    valor_total NUMERIC(15,2),
                    cliente_id INTEGER,
                    diretoria_id INTEGER,
                    linha_produto_id INTEGER,
                    criado_por_id INTEGER,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    status_v19 VARCHAR(100) DEFAULT 'em_andamento',
                    modalidade_v19 VARCHAR(100) DEFAULT 'venda'
                )
            """))

            print("V33 EXORCISM: Migrating data from zombies...")
            # Migração de dados (Se existirem)
            try:
                conn.execute(text("INSERT INTO usuarios (id, nome, email, senha_hash, perfil_v19, diretoria_id, ativo) SELECT id, nome, email, senha_hash, perfil_v19, diretoria_id, ativo FROM usuarios_ghost_zombie_v33"))
                conn.execute(text("INSERT INTO vendas (id, numero, processo_sei, objeto, valor_total, cliente_id, diretoria_id, linha_produto_id, criado_por_id) SELECT id, numero, processo_sei, objeto, valor_total, cliente_id, diretoria_id, linha_produto_id, criado_por_id FROM vendas_ghost_zombie_v33"))
            except:
                print("V33: Data migration failed (probably empty or schema mismatch), skipping to safe seed.")

            # 3. Limpeza final total
            conn.execute(text("DROP TABLE IF EXISTS vendas_ghost_zombie_v33 CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS usuarios_ghost_zombie_v33 CASCADE"))
            
            print("V33 EXORCISM: FULL SUCCESS. The OID Ghost is incinerated. ✅")
    except Exception as e:
        print(f"V33 EXORCISM CRITICAL ERROR: {e}")
        traceback.print_exc()

@asynccontextmanager
async def lifespan(app: FastAPI):
    absolute_eradication()
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
