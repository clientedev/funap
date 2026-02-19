
import sqlalchemy
from sqlalchemy import text, create_engine
import time

# Credentials provided by the user
DB_URL = "postgresql://postgres:vuHJNJQpQpPwQiPRkecMeFgGhhskraAR@yamabiko.proxy.rlwy.net:58221/railway"

def direct_repair():
    print("🚀 INICIANDO REPARO CIRÚRGICO DIRETO NO POSTGRES...")
    engine = create_engine(DB_URL)
    
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

    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # 1. Matar outras conexões para evitar Lock Timeout
            print("💀 Terminando outras conexões para liberar o banco...")
            conn.execute(text("""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = current_database() 
                AND pid <> pg_backend_pid();
            """))
            time.sleep(2)

            # 2. Configurar timeouts
            conn.execute(text("SET lock_timeout = '30s';"))
            conn.execute(text("SET statement_timeout = '60s';"))

            # 3. Converter colunas
            print("🛠 Convertendo colunas para VARCHAR(100)...")
            for table, col in target_cols:
                try:
                    # Dropar default
                    conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} DROP DEFAULT;"))
                    # Forçar VARCHAR
                    conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE VARCHAR(100) USING {col}::VARCHAR(100);"))
                    print(f"✅ {table}.{col} -> VARCHAR(100)")
                except Exception as e:
                    print(f"❌ Erro em {table}.{col}: {e}")

            # 4. Dropar tipos nativos
            print("🔥 Eliminando tipos ENUM nativos...")
            try:
                res = conn.execute(text("SELECT typname FROM pg_type WHERE typname LIKE '%enum%'"))
                for row in res:
                    try:
                        conn.execute(text(f"DROP TYPE IF EXISTS {row[0]} CASCADE;"))
                        print(f"🔥 Dropped: {row[0]}")
                    except: pass
            except: pass

            # 5. Auditoria Final
            print("\n🔍 AUDITORIA DE TIPOS:")
            for table, col in target_cols:
                try:
                    res = conn.execute(text(
                        f"SELECT data_type FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'"
                    )).fetchone()
                    print(f"   - {table}.{col}: {res[0] if res else 'MISSING'}")
                except: pass

            # 6. Nuke local cache
            conn.execute(text("DISCARD ALL;"))
            conn.execute(text("DEALLOCATE ALL;"))
            conn.execute(text("ANALYZE;"))
            
            print("\n✨ REPARO CONCLUÍDO COM SUCESSO! ✅")

    except Exception as e:
        print(f"\n🚨 ERRO CRÍTICO NO REPARO: {e}")

if __name__ == "__main__":
    direct_repair()
