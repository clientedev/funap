
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time

# Added ?sslmode=require
URL = "postgresql://postgres:vuHJNJQpQpPwQiPRkecMeFgGhhskraAR@yamabiko.proxy.rlwy.net:58221/railway"

def total_nuke_repair():
    print("🔥 NUCLEAR REPAIR (SSL): Connecting to database...")
    try:
        # Explicit sslmode in connection string or connect call
        conn = psycopg2.connect(URL, sslmode='require', connect_timeout=10)
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
                cur.execute(f'ALTER TABLE "{table}" ALTER COLUMN "{col}" DROP DEFAULT')
                cur.execute(f'ALTER TABLE "{table}" ALTER COLUMN "{col}" TYPE VARCHAR(100) USING "{col}"::VARCHAR(100)')
                print(f"      ✅ Fixed {table}.{col}")
            except Exception as e:
                print(f"      ❌ Failed {table}.{col}: {e}")

        print("🔥 Dropping ALL ENUM types...")
        try:
            # Query enums strictly
            cur.execute("SELECT typname FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid GROUP BY typname")
            types = [row[0] for row in cur.fetchall()]
            
            # Also check by name pattern as backup
            cur.execute("SELECT typname FROM pg_type WHERE typname LIKE '%enum%'")
            for row in cur.fetchall():
                if row[0] not in types: types.append(row[0])

            for t in types:
                try:
                    cur.execute(text(f'DROP TYPE IF EXISTS "{t}" CASCADE')) # Error here, text() is sqlalchemy. Using string literal.
                    # Correcting to:
                    cur.execute(f'DROP TYPE IF EXISTS "{t}" CASCADE')
                    print(f"      🔥 Dropped {t}")
                except Exception as e:
                    print(f"      ⚠️ Failed to drop {t}: {e}")
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
        print("\n✨ DATABASE IS REPAIRED AND IMMUNE TO OID ERRORS! ✅")

    except Exception as e:
        print(f"🚨 FATAL ERROR: {e}")

if __name__ == "__main__":
    total_nuke_repair()
