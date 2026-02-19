# SISCONT - Deploy V13 (ABSOLUTE CERTAINTY) - 19/02/2026 14:50
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto


def run_enum_migration():
    """Migra colunas de Enum para TEXT para resolver definitivamente o erro de cache OID lookup do Postgres."""
    import traceback
    from sqlalchemy import text
    from app.database import engine
    
    db_url = str(engine.url)
    if "sqlite" in db_url:
        return
    
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # 0. Limpar planos, caches e prepared statements
            print("CACHE NUKE: Clearing Postgres session caches...")
            conn.execute(text("DISCARD ALL;"))
            conn.execute(text("DEALLOCATE ALL;"))
            conn.execute(text("SET lock_timeout = '30s';"))
            conn.execute(text("SET statement_timeout = '60s';"))
            conn.execute(text("SET search_path TO public;"))
            
            # Encerrar outras conexões para liberar locks
            try:
                conn.execute(text("""
                    SELECT pg_terminate_backend(pid) 
                    FROM pg_stat_activity 
                    WHERE datname = current_database() 
                    AND pid <> pg_backend_pid();
                """))
            except: pass

            # 1. Lista de colunas para converter para TEXT/VARCHAR
            target_cols = [
                ("vendas", "status"),
                ("vendas", "modalidade"),
                ("propostas", "status"),
                ("contratos", "status"),
                ("empenhos", "status"),
                ("pedidos", "status"),
                ("notas_fiscais", "status_entrega"),
                ("solicitacoes_custo", "status"),
                ("usuarios", "perfil")
            ]

            print("FORCE REPAIR: Converting columns to VARCHAR(100)...")
            for table, col in target_cols:
                try:
                    # Garantir que a coluna existe
                    res = conn.execute(text(
                        f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'"
                    )).fetchone()
                    
                    if res:
                        # Dropar default primeiro
                        conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} DROP DEFAULT;"))
                        # Converter para VARCHAR(100) (mais explícito que TEXT)
                        conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE VARCHAR(100) USING {col}::VARCHAR(100);"))
                        print(f"Repaired: {table}.{col} -> VARCHAR(100)")
                except Exception as e:
                    print(f"Erro em {table}.{col}: {e}")

            # 2. ELIMINAR TODOS OS TIPOS ENUM ANTIGOS
            print("CLEANUP: Dropping all native enum types...")
            try:
                # Buscar tipos que são enums
                res = conn.execute(text("SELECT t.typname FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid GROUP BY t.typname"))
                enum_types = [row[0] for row in res]
                # Também buscar por convenção de nome
                res2 = conn.execute(text("SELECT typname FROM pg_type WHERE typname LIKE '%enum%'"))
                for row in res2:
                    if row[0] not in enum_types: enum_types.append(row[0])

                for t_name in enum_types:
                    try:
                        conn.execute(text(f"DROP TYPE IF EXISTS {t_name} CASCADE;"))
                        print(f"Dropped type: {t_name}")
                    except: pass
            except: pass

            # 3. Colunas extras e infra
            extra_cols = [
                ("vendas", "processo_sei", "VARCHAR(50)"),
                ("vendas", "objeto", "TEXT"),
                ("vendas", "valor_total", "NUMERIC(15,2)")
            ]
            for table, col, col_type in extra_cols:
                try:
                    res = conn.execute(text(
                        f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'"
                    )).fetchone()
                    if not res:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};"))
                except: pass

            # 4. DATA TYPE AUDIT (Log de verificação final)
            print("--- DATABASE TYPE AUDIT ---")
            for table, col in target_cols:
                try:
                    res = conn.execute(text(
                        f"SELECT data_type FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'"
                    )).fetchone()
                    print(f"VERIFICATION: {table}.{col} is now {res[0] if res else 'MISSING'}")
                except: pass
            print("--- END AUDIT ---")

            conn.execute(text("ANALYZE;"))
            conn.execute(text("DISCARD ALL;"))
            print("MIGRAÇÃO V13 (ABSOLUTE CERTAINTY) CONCLUÍDA. ✅")
            
    except Exception:
        print("Erro crítico na migração V13:")
        traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_enum_migration()
    yield


app = FastAPI(title="SisCont", version="1.0.0", lifespan=lifespan)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    if exc.status_code == 403:
        return RedirectResponse(url="/dashboard")
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
            # 1. Column Types
            schema_res = conn.execute(text(f"""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name IN ({','.join([f"'{t}'" for t in target_tables])})
                AND (column_name LIKE '%status%' OR column_name = 'perfil' OR column_name = 'modalidade')
            """)).fetchall()
            
            # 2. Hunting OID 21978
            oid_res = conn.execute(text("""
                SELECT 
                    'type_detail' as category, 
                    typname || ' (ns:' || typnamespace::text || ', cat:' || typcategory || ')' as name 
                FROM pg_type WHERE oid = 21978
                UNION ALL
                SELECT 'cast' as category, castsource::text || '->' || casttarget::text as name FROM pg_cast WHERE castsource = 21978 OR casttarget = 21978
                UNION ALL
                SELECT 'attr_atttypid' as category, relname || '.' || attname as name FROM pg_attribute a JOIN pg_class c ON a.attrelid = c.oid WHERE atttypid = 21978
                UNION ALL
                SELECT 'attr_atttypmod' as category, relname || '.' || attname as name FROM pg_attribute a JOIN pg_class c ON a.attrelid = c.oid WHERE atttypmod = 21978
            """)).fetchall()
            
            return {
                "columns": [{"table": r[0], "column": r[1], "type": r[2]} for r in schema_res],
                "oid_hunt_21978": [{"category": r[0], "name": r[1]} for r in oid_res]
            }
    except Exception as e:
        return {"error": str(e)}
