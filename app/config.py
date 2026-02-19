"""
SisCont - Configurações da Aplicação
Carrega variáveis de ambiente via python-dotenv.
"""
import os
from dotenv import load_dotenv
from functools import lru_cache

# Carrega .env manualmente
load_dotenv()

class Settings:
    def __init__(self):
        db_url = os.getenv("DATABASE_URL", "postgresql://siscont:siscont@db:5432/siscont")
        if db_url and db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        self.DATABASE_URL = db_url
        self.SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
        self.ALGORITHM = os.getenv("ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
        self.FIRST_ADMIN_EMAIL = os.getenv("FIRST_ADMIN_EMAIL", "admin@siscont.com")
        self.FIRST_ADMIN_PASSWORD = os.getenv("FIRST_ADMIN_PASSWORD", "admin123")
        self.FIRST_ADMIN_NOME = os.getenv("FIRST_ADMIN_NOME", "Administrador")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
