"""Modelo: Usuario."""
import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PerfilEnum(str, enum.Enum):
    admin = "admin"
    usuario = "usuario"
    comercial = "comercial"
    financeiro = "financeiro"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[PerfilEnum] = mapped_column(SAEnum(PerfilEnum, name="perfilenum_v4"), default=PerfilEnum.usuario, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    diretoria_id: Mapped[int | None] = mapped_column(ForeignKey("diretorias.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relacionamentos
    diretoria: Mapped["Diretoria"] = relationship("Diretoria", back_populates="usuarios")
