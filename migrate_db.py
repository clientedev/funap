"""
Script de Migração do Banco de Dados - Railway
Atualiza os tipos ENUM do PostgreSQL para os novos valores de status.

Uso:
  python migrate_db.py

O script lê a DATABASE_URL do .env ou da variável de ambiente.
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    print("❌ DATABASE_URL não encontrada. Configure no .env ou variável de ambiente.")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

# ============================================================
# Migração: atualizar enums do PostgreSQL e dados existentes
# ============================================================
MIGRATION_STEPS = []

# --- 1. VendaStatusEnum: ABERTA -> EM ANDAMENTO, + novos valores ---
MIGRATION_STEPS.append({
    "desc": "Atualizar VendaStatusEnum",
    "queries": [
        # Adicionar novos valores ao enum (se não existirem)
        "ALTER TYPE vendastatusenum ADD VALUE IF NOT EXISTS 'EM ANDAMENTO';",
        "ALTER TYPE vendastatusenum ADD VALUE IF NOT EXISTS 'AGUARDANDO PROPOSTA';",
        "ALTER TYPE vendastatusenum ADD VALUE IF NOT EXISTS 'AGUARDANDO EMPENHO';",
        "ALTER TYPE vendastatusenum ADD VALUE IF NOT EXISTS 'FATURADO';",
    ]
})

# --- 2. Migrar dados existentes com status antigo para novo ---
# Precisa recriar o enum pois não é possível renomear valores direto
MIGRATION_STEPS.append({
    "desc": "Migrar dados de ABERTA para EM ANDAMENTO",
    "queries": [
        # Converter coluna para TEXT temporariamente
        "ALTER TABLE vendas ALTER COLUMN status TYPE TEXT;",
        # Atualizar dados antigos
        "UPDATE vendas SET status = 'EM ANDAMENTO' WHERE status = 'ABERTA';",
        # Dropar tipo antigo
        "DROP TYPE IF EXISTS vendastatusenum;",
        # Recriar tipo com todos os valores novos
        """CREATE TYPE vendastatusenum AS ENUM (
            'EM ANDAMENTO', 'AGUARDANDO PROPOSTA', 'AGUARDANDO EMPENHO',
            'FATURADO', 'FINALIZADA', 'CANCELADA'
        );""",
        # Converter coluna de volta para ENUM
        "ALTER TABLE vendas ALTER COLUMN status TYPE vendastatusenum USING status::vendastatusenum;",
        # Restaurar default
        "ALTER TABLE vendas ALTER COLUMN status SET DEFAULT 'EM ANDAMENTO';",
    ]
})

# --- 3. ContratoStatusEnum: ativo -> ATIVO, encerrado -> ENCERRADO, cancelado -> CANCELADO ---
MIGRATION_STEPS.append({
    "desc": "Atualizar ContratoStatusEnum",
    "queries": [
        "ALTER TABLE contratos ALTER COLUMN status TYPE TEXT;",
        "UPDATE contratos SET status = UPPER(status) WHERE status != UPPER(status);",
        "DROP TYPE IF EXISTS contratostatusenum;",
        "CREATE TYPE contratostatusenum AS ENUM ('ATIVO', 'ENCERRADO', 'CANCELADO');",
        "ALTER TABLE contratos ALTER COLUMN status TYPE contratostatusenum USING status::contratostatusenum;",
        "ALTER TABLE contratos ALTER COLUMN status SET DEFAULT 'ATIVO';",
    ]
})

# --- 4. EmpenhoStatusEnum: pendente -> PENDENTE, emitido -> EMITIDO, cancelado -> CANCELADO ---
MIGRATION_STEPS.append({
    "desc": "Atualizar EmpenhoStatusEnum",
    "queries": [
        "ALTER TABLE empenhos ALTER COLUMN status TYPE TEXT;",
        "UPDATE empenhos SET status = UPPER(status) WHERE status != UPPER(status);",
        "DROP TYPE IF EXISTS empenhostatusenum;",
        "CREATE TYPE empenhostatusenum AS ENUM ('PENDENTE', 'EMITIDO', 'CANCELADO');",
        "ALTER TABLE empenhos ALTER COLUMN status TYPE empenhostatusenum USING status::empenhostatusenum;",
        "ALTER TABLE empenhos ALTER COLUMN status SET DEFAULT 'PENDENTE';",
    ]
})

# --- 5. SolicitacaoCustoStatusEnum ---
MIGRATION_STEPS.append({
    "desc": "Atualizar SolicitacaoCustoStatusEnum",
    "queries": [
        "ALTER TABLE solicitacoes_custo ALTER COLUMN status TYPE TEXT;",
        "UPDATE solicitacoes_custo SET status = UPPER(status) WHERE status != UPPER(status);",
        "DROP TYPE IF EXISTS solicitacaocustostatusenum;",
        "CREATE TYPE solicitacaocustostatusenum AS ENUM ('PENDENTE', 'APROVADA', 'RECUSADA');",
        "ALTER TABLE solicitacoes_custo ALTER COLUMN status TYPE solicitacaocustostatusenum USING status::solicitacaocustostatusenum;",
        "ALTER TABLE solicitacoes_custo ALTER COLUMN status SET DEFAULT 'PENDENTE';",
    ]
})

# --- 6. Adicionar perfis de usuário (comercial, financeiro) ---
MIGRATION_STEPS.append({
    "desc": "Adicionar novos perfis de usuário",
    "queries": [
        "ALTER TYPE perfilenum ADD VALUE IF NOT EXISTS 'comercial';",
        "ALTER TYPE perfilenum ADD VALUE IF NOT EXISTS 'financeiro';",
    ]
})


def run_migration():
    print("=" * 60)
    print("  SISCONT - Migração do Banco de Dados")
    print("=" * 60)
    print(f"\n📌 Conectando em: {DATABASE_URL[:40]}...")
    
    with engine.connect() as conn:
        for i, step in enumerate(MIGRATION_STEPS, 1):
            print(f"\n🔄 Passo {i}/{len(MIGRATION_STEPS)}: {step['desc']}")
            for query in step["queries"]:
                try:
                    conn.execute(text(query))
                    conn.commit()
                    print(f"   ✅ {query[:70]}...")
                except Exception as e:
                    error_msg = str(e)
                    # Ignorar erros de "já existe" pois são idempotentes
                    if "already exists" in error_msg or "DuplicateObject" in error_msg:
                        conn.rollback()
                        print(f"   ⏭️  Já existe, pulando: {query[:50]}...")
                    elif "does not exist" in error_msg and ("DROP TYPE" in query or "ALTER TYPE" in query):
                        conn.rollback()
                        print(f"   ⏭️  Tipo não existe, pulando: {query[:50]}...")
                    else:
                        conn.rollback()
                        print(f"   ❌ Erro: {error_msg}")
                        print(f"      Query: {query}")
                        raise
    
    print("\n" + "=" * 60)
    print("  ✅ Migração concluída com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
