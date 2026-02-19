from app.database import engine, Base
from app.models import *

def create_tables():
    print("Aguardando inicialização do banco de dados para criar tabelas...")
    try:
        # Tenta criar todas as tabelas definidas nos modelos herdados de Base
        Base.metadata.create_all(bind=engine)
        print("Tabelas verificadas/criadas com sucesso!")
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")

if __name__ == "__main__":
    create_tables()
