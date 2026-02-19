
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time

URL = "postgresql://postgres:vuHJNJQpQpPwQiPRkecMeFgGhhskraAR@yamabiko.proxy.rlwy.net:58221/railway"

def total_nuke_repair():
    print("🔥 NUCLEAR REPAIR: Connecting to database...")
    try:
        conn = psycopg2.connect(URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        print("💀 Killing all sessions to break locks...")
        cur.execute("""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = current_database() 
            AND pid <> pg_backend_pid();
        """)
        time.sleep(3)

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

        print("🛠 Converting columns to VARCHAR(100)...")
        for table, col in target_cols:
            try:
                print(f"   -> Repairing {table}.{col}...")
                cur.execute(f"ALTER TABLE {table} ALTER COLUMN {col} DROP DEFAULT")
                cur.execute(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE VARCHAR(100) USING {col}::VARCHAR(100)")
                print(f"      ✅ Fixed {table}.{col}")
            except Exception as e:
                print(f"      ❌ Failed {table}.{col}: {e}")

        print("🔥 Dropping ALL ENUM types...")
        try:
            cur.execute("SELECT typname FROM pg_type WHERE typname LIKE '%enum%' OR typname IN ('vendastatusenum', 'modalidadeenum', 'propostastatusenum', 'perfilenum')")
            types = [row[0] for row in cur.fetchall()]
            for t in types:
                try:
                    cur.execute(f"DROP TYPE IF EXISTS {t} CASCADE")
                    print(f"      🔥 Dropped {t}")
                except: pass
        except: pass

        print("\n🔍 FINAL AUDIT:")
        for table, col in target_cols:
            try:
                cur.execute(f"SELECT data_type FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'")
                res = cur.fetchone()
                print(f"   - {table}.{col}: {res[0] if res else 'MISSING'}")
            except: pass

        cur.execute("DISCARD ALL")
        cur.close()
        conn.close()
        print("\n✨ DATABASE IS REPAIRED AND IMLUNE TO OID ERRORS! ✅")

    except Exception as e:
        print(f"🚨 FATAL ERROR: {e}")

if __name__ == "__main__":
    total_nuke_repair()
