"""
SisCont - Configuração do Banco de Dados
Engine SQLAlchemy + Session Factory.
"""
from sqlalchemy import create_engine
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
