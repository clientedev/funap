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

# --- SOLUÇÃO CIRÚRGICA PARA OID CACHE (V22) ---
if not settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def connect_listener(dbapi_connection, connection_record):
        """
        Garante que toda nova conexão ou conexão retirada do pool limpe seus caches internos do Postgres.
        Isso mata o erro 'cache lookup failed for type 21978' na raiz.
        """
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("DEALLOCATE ALL;")
            cursor.execute("DISCARD ALL;")
        except:
            pass
        finally:
            cursor.close()
# ---------------------------------------------

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
