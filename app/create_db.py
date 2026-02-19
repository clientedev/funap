"""Script para criação manual das tabelas no SQLite."""
from app.database import engine, Base
from app.models import *

def create_tables():
    print("Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso.")

if __name__ == "__main__":
    create_tables()
