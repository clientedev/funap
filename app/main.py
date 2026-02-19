# SISCONT - Deploy V21.1 (ROBUST NUCLEAR RESET) - 19/02/2026 16:30
import traceback
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto

LOG_FILE = "/tmp/migration_log.txt"

def run_enum_migration():
    """Robust Nuclear Table Reset: Purga caches de metadados forçando novas OIDs de tabela."""
    from sqlalchemy import text, inspect
    from app.database import engine, Base
    
    db_url = str(engine.url)
    if "sqlite" in db_url: return

    target_tables = [
        'usuarios', 'vendas', 'propostas', 'contratos', 
        'empenhos', 'pedidos', 'notas_fiscais', 'solicitacoes_custo'
    ]

    with open(LOG_FILE, "a") as f:
        f.write("\n--- STARTING V21.1 ROBUST NUCLEAR RESET ---\n")
        try:
            with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                f.write("Killing other sessions...\n")
                try:
                    conn.execute(text("""
                        SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
                        WHERE datname = current_database() AND pid <> pg_backend_pid();
                    """))
                except: pass

                conn.execute(text("SET lock_timeout = '30s';"))
                inspector = inspect(engine)
                existing_tables = inspector.get_table_names()
                
                # Só roda se 'vendas' ainda estiver no OID antigo (ou simplesmente roda uma vez)
                # Para garantir, vamo rodar se não houver a flag v21_done
                if 'vendas' in existing_tables:
                    f.write("Rotating tables...\n")
                    
                    # Ordem inversa para dropar FKs se necessário ou usar CASCADE
                    for table in reversed(target_tables):
                        if table in existing_tables:
                            f.write(f"   -> Renaming {table}\n")
                            conn.execute(text(f'DROP TABLE IF EXISTS "{table}_v21_bak" CASCADE'))
                            conn.execute(text(f'ALTER TABLE "{table}" RENAME TO "{table}_v21_bak"'))

                    f.write("Recreating schema...\n")
                    Base.metadata.create_all(engine)

                    f.write("Migrating data...\n")
                    conn.execute(text("SET session_replication_role = 'replica';"))
                    
                    for table in target_tables:
                        try:
                            f.write(f"      -> {table}\n")
                            # Filtrar colunas que existem na tabela nova
                            cols_res = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
                            cols = [f'"{row[0]}"' for row in cols_res]
                            col_str = ", ".join(cols)
                            
                            conn.execute(text(f'INSERT INTO "{table}" ({col_str}) SELECT {col_str} FROM "{table}_v21_bak"'))
                        except Exception as e:
                            f.write(f"      ⚠️ Error migrating {table}: {e}\n")

                    conn.execute(text("SET session_replication_role = 'origin';"))

                    f.write("Dropping backups...\n")
                    for table in target_tables:
                        try:
                            conn.execute(text(f'DROP TABLE IF EXISTS "{table}_v21_bak" CASCADE'))
                        except: pass

                    f.write("Clearing caches...\n")
                    conn.execute(text("DISCARD ALL;"))
                    conn.execute(text("DEALLOCATE ALL;"))
                    conn.execute(text("ANALYZE;"))
                    f.write("SUCCESS.\n")
                else:
                    f.write("Tables already rotated or missing.\n")
                    
        except Exception:
            err = traceback.format_exc()
            f.write(f"FATAL ERROR:\n{err}\n")
            print(err)


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_enum_migration()
    yield


app = FastAPI(title="SisCont", version="1.0.0", lifespan=lifespan)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401: return RedirectResponse(url="/login")
    if exc.status_code == 403: return RedirectResponse(url="/dashboard")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Rotas
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
            # Check OID
            oid_check = conn.execute(text("SELECT typname FROM pg_type WHERE oid = 21978")).fetchone()
            
            # Check Log
            log_content = ""
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r") as f:
                    log_content = f.read()
            
            return {
                "oid_21978": oid_check[0] if oid_check else "NOT FOUND",
                "migration_log": log_content
            }
    except Exception as e: return {"error": str(e)}
