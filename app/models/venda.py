"""Modelo: Venda - entidade central do sistema."""
import enum
from datetime import datetime
from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class VendaStatusEnum(str, enum.Enum):
    em_andamento = "em_andamento"
    aguardando_proposta = "aguardando_proposta"
    aguardando_empenho = "aguardando_empenho"
    faturado = "faturado"
    finalizada = "finalizada"
    cancelada = "cancelada"


class ModalidadeEnum(str, enum.Enum):
    venda = "venda"
    licitacao = "licitacao"
    producao = "producao"


class Venda(Base):
    __tablename__ = "vendas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    processo_sei: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    objeto: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VendaStatusEnum] = mapped_column(
        SAEnum(VendaStatusEnum, name="vendastatusenum_v5"), default=VendaStatusEnum.em_andamento, nullable=False, index=True
    )
    modalidade: Mapped[ModalidadeEnum] = mapped_column(
        SAEnum(ModalidadeEnum, name="modalidadeenum_v5"), default=ModalidadeEnum.venda, nullable=False, index=True
    )
    valor_total: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Chaves estrangeiras
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False, index=True)
    diretoria_id: Mapped[int] = mapped_column(ForeignKey("diretorias.id"), nullable=False, index=True)
    linha_produto_id: Mapped[int | None] = mapped_column(ForeignKey("linhas_produto.id"), nullable=True, index=True)
    criado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relacionamentos
    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="vendas")
    diretoria: Mapped["Diretoria"] = relationship("Diretoria", back_populates="vendas")
    linha_produto: Mapped["LinhaProduto"] = relationship("LinhaProduto", back_populates="vendas")
    criado_por: Mapped["Usuario"] = relationship("Usuario", foreign_keys=[criado_por_id])

    solicitacoes_custo: Mapped[list["SolicitacaoCusto"]] = relationship(
        "SolicitacaoCusto", back_populates="venda", cascade="all, delete-orphan"
    )
    propostas: Mapped[list["Proposta"]] = relationship(
        "Proposta", back_populates="venda", cascade="all, delete-orphan"
    )
    contratos: Mapped[list["Contrato"]] = relationship(
        "Contrato", back_populates="venda", cascade="all, delete-orphan"
    )
    empenhos: Mapped[list["Empenho"]] = relationship(
        "Empenho", back_populates="venda", cascade="all, delete-orphan"
    )
    pedidos: Mapped[list["Pedido"]] = relationship(
        "Pedido", back_populates="venda", cascade="all, delete-orphan"
    )
    notas_fiscais: Mapped[list["NotaFiscal"]] = relationship(
        "NotaFiscal", back_populates="venda", cascade="all, delete-orphan"
    )
