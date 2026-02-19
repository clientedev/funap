
from sqlalchemy import text, create_engine

DB_URL = "postgresql://postgres:vuHJNJQpQpPwQiPRkecMeFgGhhskraAR@yamabiko.proxy.rlwy.net:58221/railway"

def audit():
    engine = create_engine(DB_URL)
    target_cols = [
        ("vendas", "status"),
        ("vendas", "modalidade"),
        ("propostas", "status"),
        ("usuarios", "perfil")
    ]
    print("\n🔍 AUDITORIA DE TIPOS ATUAIS:")
    with engine.connect() as conn:
        for table, col in target_cols:
            try:
                res = conn.execute(text(
                    f"SELECT data_type FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'"
                )).fetchone()
                print(f"   - {table}.{col}: {res[0] if res else 'MISSING'}")
            except Exception as e:
                print(f"❌ Erro auditando {table}.{col}: {e}")

if __name__ == "__main__":
    audit()
