from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto


def run_enum_migration():
    """Migra enums do PostgreSQL para os novos valores na inicialização."""
    import traceback
    from sqlalchemy import text
    from app.database import engine
    
    db_url = str(engine.url)
    if "sqlite" in db_url:
        return  # SQLite não tem enums nativos
    
    # Lista de tabelas e colunas que usam enums customizados
    target_columns = [
        ("vendas", "status", "vendastatusenum"),
        ("vendas", "modalidade", "modalidadeenum"),
        ("propostas", "status", "propostastatusenum"),
        ("contratos", "status", "contratostatusenum"),
        ("empenhos", "status", "empenhostatusenum"),
        ("pedidos", "status", "pedidostatusenum"),
        ("notas_fiscais", "status_entrega", "nfestatusentregaenum"),
        ("solicitacoes_custo", "status", "solicitacaocustostatusenum"),
        # PerfilEnum em usuarios já é minúsculo, mas vamos garantir o tipo se necessário
    ]
    
    # Definição dos novos enums (todos os labels em minúsculo)
    enums_to_recreate = {
        "vendastatusenum": ["em_andamento", "aguardando_proposta", "aguardando_empenho", "faturado", "finalizada", "cancelada"],
        "modalidadeenum": ["venda", "licitacao", "producao"],
        "propostastatusenum": ["pendente", "aprovada", "cancelada"],
        "contratostatusenum": ["ativo", "encerrado", "cancelado"],
        "empenhostatusenum": ["pendente", "emitido", "cancelado"],
        "pedidostatusenum": ["pendente", "finalizado"],
        "nfestatusentregaenum": ["pendente", "entrega parcial", "entrega total"],
        "solicitacaocustostatusenum": ["pendente", "aprovada", "recusada"],
    }
    
    try:
        with engine.connect() as conn:
            # 1. Converter todas as colunas para TEXT para poder dropar os tipos
            for table, col, _ in target_columns:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE TEXT;"))
                    conn.commit()
                except Exception:
                    conn.rollback()
            
            # 2. Dropar e Recriar os Tipos
            for type_name, labels in enums_to_recreate.items():
                labels_str = ", ".join([f"'{l}'" for l in labels])
                try:
                    conn.execute(text(f"DROP TYPE IF EXISTS {type_name} CASCADE;"))
                    conn.execute(text(f"CREATE TYPE {type_name} AS ENUM ({labels_str});"))
                    conn.commit()
                except Exception:
                    conn.rollback()
            
            # 3. Limpar e Normalizar os dados (converter tudo para minúsculo e tratar nomes antigos)
            normalization_queries = [
                # Vendas
                "UPDATE vendas SET status = 'em_andamento' WHERE status IN ('ABERTA', 'aberta', 'PROPOSTA EM ANÁLISE', 'EM ANDAMENTO', 'EM_ANDAMENTO');",
                "UPDATE vendas SET status = 'finalizada' WHERE UPPER(status) = 'FINALIZADA';",
                "UPDATE vendas SET status = 'cancelada' WHERE UPPER(status) = 'CANCELADA';",
                "UPDATE vendas SET status = 'aguardando_proposta' WHERE UPPER(status) = 'AGUARDANDO PROPOSTA';",
                "UPDATE vendas SET status = 'aguardando_empenho' WHERE UPPER(status) = 'AGUARDANDO EMPENHO';",
                "UPDATE vendas SET status = 'faturado' WHERE UPPER(status) IN ('FATURADO', 'EMPENHADO', 'PEDIDO EMITIDO');",
                "UPDATE vendas SET status = 'em_andamento' WHERE status NOT IN ('em_andamento', 'aguardando_proposta', 'aguardando_empenho', 'faturado', 'finalizada', 'cancelada');",
                
                # Propostas
                "UPDATE propostas SET status = 'pendente' WHERE UPPER(status) = 'PENDENTE';",
                "UPDATE propostas SET status = 'aprovada' WHERE UPPER(status) = 'APROVADA';",
                "UPDATE propostas SET status = 'cancelada' WHERE UPPER(status) = 'CANCELADA';",
                "UPDATE propostas SET status = 'pendente' WHERE status NOT IN ('pendente', 'aprovada', 'cancelada');",
                
                # Notas Fiscais (tratamento especial para espaços)
                "UPDATE notas_fiscais SET status_entrega = 'entrega parcial' WHERE UPPER(status_entrega) IN ('ENTREGA PARCIAL', 'PARCIAL');",
                "UPDATE notas_fiscais SET status_entrega = 'entrega total' WHERE UPPER(status_entrega) IN ('ENTREGA TOTAL', 'TOTAL');",
                "UPDATE notas_fiscais SET status_entrega = 'pendente' WHERE UPPER(status_entrega) = 'PENDENTE' OR status_entrega NOT IN ('pendente', 'entrega parcial', 'entrega total');",
            ]
            
            # Normalizar outras tabelas genericamente para minúsculo
            for table, col, _ in target_columns:
                if table not in ["vendas", "notas_fiscais", "propostas"]:
                    normalization_queries.append(f"UPDATE {table} SET {col} = LOWER({col});")
            
            for query in normalization_queries:
                try:
                    conn.execute(text(query))
                    conn.commit()
                except Exception:
                    conn.rollback()
            
            # 4. Converter as colunas de volta para os tipos ENUM
            for table, col, type_name in target_columns:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE {type_name} USING {col}::{type_name};"))
                    # Set defaults
                    default_val = 'em_andamento' if table == 'vendas' else ('ativo' if table == 'contratos' else 'pendente')
                    conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} SET DEFAULT '{default_val}';"))
                    conn.commit()
                except Exception:
                    conn.rollback()
                    
            # 5. Adicionar valores ao PerfilEnum se faltarem
            try:
                conn.execute(text("ALTER TYPE perfilenum ADD VALUE IF NOT EXISTS 'comercial';"))
                conn.execute(text("ALTER TYPE perfilenum ADD VALUE IF NOT EXISTS 'financeiro';"))
                conn.commit()
            except Exception:
                conn.rollback()

        print("[MIGRATION] Robust enum migration completed successfully.")
    except Exception:
        print(f"[MIGRATION ERROR] {traceback.format_exc()}")


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
    # Para outros erros (404, 500, etc), mostrar o erro real
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"[ERROR 500] {request.url}: {traceback.format_exc()}")
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": str(exc)})

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(diretorias.router)
app.include_router(usuarios.router)
app.include_router(vendas.router)
app.include_router(clientes.router)
app.include_router(linhas_produto.router)
