"""Modelo: Empenho."""
import enum
from datetime import datetime, date
from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, Enum as SAEnum, func, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class EmpenhoStatusEnum(str, enum.Enum):
    pendente = "pendente"
    emitido = "emitido"
    cancelado = "cancelado"


class Empenho(Base):
    __tablename__ = "empenhos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    venda_id: Mapped[int] = mapped_column(ForeignKey("vendas.id"), nullable=False, index=True)
    numero: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    valor: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    data_emissao: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_recebimento: Mapped[date | None] = mapped_column(Date, nullable=True)
    prazo_entrega: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[EmpenhoStatusEnum] = mapped_column(
        SAEnum(EmpenhoStatusEnum, name="empenhostatusenum_v5"), default=EmpenhoStatusEnum.pendente, nullable=False, index=True
    )
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    venda: Mapped["Venda"] = relationship("Venda", back_populates="empenhos")
