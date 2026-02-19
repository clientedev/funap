"""Script para reset completo do banco de dados (Drop & Create)."""
from app.database import engine, Base
from app.models import *

def reset_database():
    print("Derrubando todas as tabelas...")
    Base.metadata.drop_all(bind=engine)
    print("Recriando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("Banco de dados resetado com sucesso!")

if __name__ == "__main__":
    reset_database()
