# SISCONT - Deploy V21 (NUCLEAR TABLE RESET) - 19/02/2026 16:15
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto


def run_enum_migration():
    """Nuclear Table Reset: Re-cria tabelas para limpar definitivamente metadados corrompidos de OID."""
    import traceback
    from sqlalchemy import text, inspect
    from app.database import engine, Base
    
    db_url = str(engine.url)
    if "sqlite" in db_url: return

    target_tables = [
        'vendas', 'usuarios', 'propostas', 'contratos', 
        'empenhos', 'pedidos', 'notas_fiscais', 'solicitacoes_custo'
    ]

    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print("NUCLEAR RESET V21: Initiating table rotation...")
            conn.execute(text("SET lock_timeout = '50s';"))
            
            # 1. Renomear tabelas atuais para _dead_oid
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            tables_to_migrate = []
            for table in target_tables:
                if table in existing_tables:
                    # Se a tabela _dead_oid já existe de um crash anterior, dropa ela
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table}_dead_oid" CASCADE'))
                    print(f"   -> Rotating {table} to {table}_dead_oid")
                    conn.execute(text(f'ALTER TABLE "{table}" RENAME TO "{table}_dead_oid"'))
                    tables_to_migrate.append(table)

            # 2. Criar tabelas novas (Limpas, sem OIDs antigos)
            print("   -> Creating fresh tables...")
            Base.metadata.create_all(engine)

            # 3. Migrar dados
            # NOTA: Precisamos migrar em ordem de dependência ou desativar FKs temporariamente
            conn.execute(text("SET session_replication_role = 'replica';")) # Desativa triggers/FKs
            
            # Ordem de migração segura
            migration_order = [
                'usuarios', 'vendas', 'propostas', 'contratos', 
                'empenhos', 'pedidos', 'notas_fiscais', 'solicitacoes_custo'
            ]
            
            for table in migration_order:
                if table in tables_to_migrate:
                    print(f"   -> Migrating data for {table}...")
                    # Pega as colunas da tabela NOVA para garantir que não tentamos inserir no que não existe
                    cols_res = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
                    cols = [row[0] for row in cols_res]
                    col_str = ", ".join([f'"{c}"' for c in cols])
                    
                    # Insert from old to new. 
                    # Se colunas v19 existirem na antiga, ok. Se não, ignoramos (já lidado em v19/v20)
                    try:
                        conn.execute(text(f'INSERT INTO "{table}" ({col_str}) SELECT {col_str} FROM "{table}_dead_oid"'))
                        print(f"      ✅ Data migrated for {table}")
                    except Exception as e:
                        print(f"      ⚠️ Migration error for {table}: {e}")

            conn.execute(text("SET session_replication_role = 'origin';"))

            # 4. Drop tables antigas
            for table in tables_to_migrate:
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}_dead_oid" CASCADE'))
                print(f"   -> Dropped legacy {table}")

            # 5. Reset Caches
            conn.execute(text("DISCARD ALL;"))
            conn.execute(text("DEALLOCATE ALL;"))
            conn.execute(text("ANALYZE;"))
            print("NUCLEAR RESET V21 CONCLUÍDO. O sistema está agora em um estado virgem de metadados. ✅")
            
    except Exception:
        print("Erro crítico no NUCLEAR RESET V21:")
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
    target_tables = ['vendas', 'propostas', 'contratos', 'empenhos', 'pedidos', 'notas_fiscais', 'solicitacoes_custo', 'usuarios']
    try:
        with engine.connect() as conn:
            schema_res = conn.execute(text(f"""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name IN ({','.join([f"'{t}'" for t in target_tables])})
                AND (column_name LIKE '%v19%' OR column_name LIKE '%status%' OR column_name = 'perfil' OR column_name = 'modalidade')
            """)).fetchall()
            
            oid_check = conn.execute(text("SELECT typname FROM pg_type WHERE oid = 21978")).fetchone()
            
            return {
                "columns": [{"table": r[0], "column": r[1], "type": r[2]} for r in schema_res],
                "oid_21978": oid_check[0] if oid_check else "NOT FOUND"
            }
    except Exception as e: return {"error": str(e)}
