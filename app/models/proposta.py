"""Modelo: Proposta Comercial."""
import enum
import enum
from datetime import datetime, date
from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, Enum as SAEnum, func, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PropostaStatusEnum(str, enum.Enum):
    pendente = "PENDENTE"
    aprovada = "APROVADA"
    cancelada = "CANCELADA"


class Proposta(Base):
    __tablename__ = "propostas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    venda_id: Mapped[int] = mapped_column(ForeignKey("vendas.id"), nullable=False, index=True)
    numero: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    revisao: Mapped[str | None] = mapped_column(String(20), nullable=True)
    valor: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    status: Mapped[PropostaStatusEnum] = mapped_column(
        SAEnum(PropostaStatusEnum), default=PropostaStatusEnum.pendente, nullable=False, index=True
    )
    data_emissao: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_validade: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    venda: Mapped["Venda"] = relationship("Venda", back_populates="propostas")
