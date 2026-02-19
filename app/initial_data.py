"""Script para inicialização de dados (Seeding)."""
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.usuario import Usuario, PerfilEnum
from app.models.diretoria import Diretoria
from app.auth.security import get_password_hash
from app.config import get_settings

settings = get_settings()

def init_db():
    db = SessionLocal()
    try:
        # 1. Criar Diretoria inicial
        admin_diretoria = db.query(Diretoria).filter(Diretoria.nome == "Diretoria Geral").first()
        if not admin_diretoria:
            admin_diretoria = Diretoria(
                nome="Diretoria Geral",
                descricao="Diretoria de Administração Central"
            )
            db.add(admin_diretoria)
            db.commit()
            db.refresh(admin_diretoria)
            print("Diretoria Geral criada.")

        # 2. Criar Admin inicial
        admin_user = db.query(Usuario).filter(Usuario.email == settings.FIRST_ADMIN_EMAIL).first()
        if not admin_user:
            admin_user = Usuario(
                nome=settings.FIRST_ADMIN_NOME,
                email=settings.FIRST_ADMIN_EMAIL,
                senha_hash=get_password_hash(settings.FIRST_ADMIN_PASSWORD),
                perfil=PerfilEnum.admin,
                diretoria_id=admin_diretoria.id
            )
            db.add(admin_user)
            db.commit()
            print(f"Admin inicial criado: {settings.FIRST_ADMIN_EMAIL}")
        else:
            print("Admin inicial já existe.")

    except Exception as e:
        print(f"Erro ao inicializar dados: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
