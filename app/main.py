# SISCONT - Deploy V19 (ABYSSAL ABANDONMENT) - 19/02/2026 15:30
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto


def run_enum_migration():
    """Migra dados para colunas novas (v19) para abandonar as corrompidas."""
    import traceback
    from sqlalchemy import text
    from app.database import engine
    
    db_url = str(engine.url)
    if "sqlite" in db_url: return

    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print("CACHE NUKE: Clearing Postgres session caches...")
            conn.execute(text("DISCARD ALL;"))
            conn.execute(text("DEALLOCATE ALL;"))
            conn.execute(text("SET lock_timeout = '50s';"))
            
            # Encerrar outras conexões
            try:
                conn.execute(text("""
                    SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
                    WHERE datname = current_database() AND pid <> pg_backend_pid();
                """))
            except: pass

            # Lista de migração: (Tabela, ColunaAntiga, ColunaNova)
            migration_plan = [
                ("vendas", "status", "status_v19"),
                ("vendas", "modalidade", "modalidade_v19"),
                ("propostas", "status", "status_v19"),
                ("contratos", "status", "status_v19"),
                ("empenhos", "status", "status_v19"),
                ("pedidos", "status", "status_v19"),
                ("notas_fiscais", "status_entrega", "status_entrega_v19"),
                ("solicitacoes_custo", "status", "status_v19"),
                ("usuarios", "perfil", "perfil_v19")
            ]

            print("ABYSSAL ABANDONMENT: Creating new columns and migrating data...")
            for table, old_col, new_col in migration_plan:
                try:
                    # 1. Garantir que a coluna NOVA existe (VARCHAR 100)
                    res = conn.execute(text(f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{new_col}'")).fetchone()
                    if not res:
                        print(f"   -> Creating {table}.{new_col}")
                        conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "{new_col}" VARCHAR(100)'))
                    
                    # 2. Migrar dados da antiga para a nova (se a antiga existir)
                    old_exists = conn.execute(text(f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{old_col}'")).fetchone()
                    if old_exists:
                        print(f"   -> Migrating {table}.{old_col} to {new_col}")
                        conn.execute(text(f'UPDATE "{table}" SET "{new_col}" = "{old_col}"::TEXT WHERE "{new_col}" IS NULL'))
                    
                    print(f"      ✅ Migrated {table}.{new_col}")
                except Exception as e:
                    print(f"      ⚠️ Skip/Error in {table}.{new_col}: {e}")

            print("MIGRAÇÃO V19 (ABANDONMENT) CONCLUÍDA. ✅")
            
    except Exception:
        print("Erro crítico na migração V19:")
        traceback.print_exc()


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

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"[ERROR 500] {request.url}: {traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": str(exc)})

app.mount("/static", StaticFiles(directory="app/static"), name="static")

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
    target_tables = ['vendas', 'propostas', 'contratos', 'empenhos', 'pedidos', 'notas_fiscais', 'solicitacoes_custo', 'usuarios']
    try:
        with engine.connect() as conn:
            schema_res = conn.execute(text(f"""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name IN ({','.join([f"'{t}'" for t in target_tables])})
                AND (column_name LIKE '%v19%' OR column_name LIKE '%status%' OR column_name = 'perfil' OR column_name = 'modalidade')
            """)).fetchall()
            return {"columns": [{"table": r[0], "column": r[1], "type": r[2]} for r in schema_res]}
    except Exception as e: return {"error": str(e)}
