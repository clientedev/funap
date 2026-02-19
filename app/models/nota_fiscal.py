"""Modelo: Nota Fiscal.
Inclui Listener SQLAlchemy para atualizar Venda quando status_entrega='total'.
"""
import enum
from datetime import datetime, date
from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, Enum as SAEnum, func, Date, event
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from app.database import Base
from app.models.venda import Venda, VendaStatusEnum


class NFEStatusEntregaEnum(str, enum.Enum):
    pendente = "pendente"
    parcial = "parcial"
    total = "total"


class NotaFiscal(Base):
    __tablename__ = "notas_fiscais"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    venda_id: Mapped[int] = mapped_column(ForeignKey("vendas.id"), nullable=False, index=True)
    numero: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    valor: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    data_emissao: Mapped[date | None] = mapped_column(Date, nullable=True)
    status_entrega: Mapped[NFEStatusEntregaEnum] = mapped_column(
        SAEnum(NFEStatusEntregaEnum, native_enum=False), name="status_entrega_v19", default=NFEStatusEntregaEnum.pendente, nullable=False, index=True
    )
    chave_acesso: Mapped[str | None] = mapped_column(String(44), nullable=True)
    documento_pdf: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    venda: Mapped["Venda"] = relationship("Venda", back_populates="notas_fiscais")


# Evento SQLAlchemy: Quando atualizar para total, fecha a venda.
def after_insert_or_update_nf(mapper, connection, target: NotaFiscal):
    if target.status_entrega == NFEStatusEntregaEnum.total:
        # Precisamos fazer update na tabela de Vendas
        connection.execute(
            Venda.__table__.update().
            where(Venda.id == target.venda_id).
            values(status=VendaStatusEnum.finalizada)
        )

event.listen(NotaFiscal, "after_insert", after_insert_or_update_nf)
event.listen(NotaFiscal, "after_update", after_insert_or_update_nf)
