"""Modelo: SolicitacaoCusto."""
import enum
from datetime import datetime, date
from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, Enum as SAEnum, func, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SolicitacaoCustoStatusEnum(str, enum.Enum):
    pendente = "pendente"
    aprovada = "aprovada"
    recusada = "recusada"


class SolicitacaoCusto(Base):
    __tablename__ = "solicitacoes_custo"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    venda_id: Mapped[int] = mapped_column(ForeignKey("vendas.id"), nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_estimado: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    data_solicitacao: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_resposta: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[SolicitacaoCustoStatusEnum] = mapped_column(
        SAEnum(SolicitacaoCustoStatusEnum, name="solicitacaocustostatusenum_v4"), default=SolicitacaoCustoStatusEnum.pendente, nullable=False
    )
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    venda: Mapped["Venda"] = relationship("Venda", back_populates="solicitacoes_custo")
