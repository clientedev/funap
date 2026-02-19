"""
SisCont - Configuração do Banco de Dados
Engine SQLAlchemy + Session Factory.
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    **({"pool_size": 10, "max_overflow": 20} if not settings.DATABASE_URL.startswith("sqlite") else {}),
    connect_args=connect_args
)

# --- SOLUÇÃO ROBUSTA PARA TRANSACTION ABORT & OID CACHE (V27) ---
if not settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "checkout")
    def checkout_listener(dbapi_connection, connection_record, connection_proxy):
        """
        Garante que toda conexão retirada do pool esteja limpa.
        O checkout_listener é mais seguro que o connect_listener pois roda em cada requisição.
        """
        cursor = dbapi_connection.cursor()
        try:
            # Se a conexão estiver em estado de erro (InFailedSqlTransaction), o rollback limpa.
            dbapi_connection.rollback()
            cursor.execute("DEALLOCATE ALL;")
            cursor.execute("DISCARD ALL;")
        except Exception:
            # Se falhar aqui, tentamos um rollback final forçado
            try: dbapi_connection.rollback()
            except: pass
        finally:
            cursor.close()
# -------------------------------------------------------------

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency para injeção de sessão do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
