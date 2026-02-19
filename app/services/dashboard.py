"""Serviço de Dashboard para Indicadores."""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.venda import Venda, VendaStatusEnum
from app.models.proposta import Proposta, PropostaStatusEnum
from app.models.pedido import Pedido, PedidoStatusEnum
from app.models.nota_fiscal import NotaFiscal, NFEStatusEntregaEnum

def get_dashboard_metrics(db: Session, diretoria_id: int | None = None):
    """
    Retorna métricas consolidadas. Se diretoria_id for passado, filtra por diretoria.
    """
    filters = []
    if diretoria_id:
        filters.append(Venda.diretoria_id == diretoria_id)

    # Vendas Abertas
    vendas_abertas = db.query(func.count(Venda.id)).filter(
        Venda.status == VendaStatusEnum.aberta, *filters
    ).scalar()

    # Vendas Finalizadas
    vendas_finalizadas = db.query(func.count(Venda.id)).filter(
        Venda.status == VendaStatusEnum.finalizada, *filters
    ).scalar()

    # Propostas Pendentes (join necessário se filtrar por diretoria na venda)
    propostas_pendentes_query = db.query(func.count(Proposta.id)).join(Venda)
    if diretoria_id:
        propostas_pendentes_query = propostas_pendentes_query.filter(Venda.diretoria_id == diretoria_id)
    propostas_pendentes = propostas_pendentes_query.filter(
        Proposta.status == PropostaStatusEnum.pendente
    ).scalar()

    # Pedidos Pendentes
    pedidos_pendentes_query = db.query(func.count(Pedido.id)).join(Venda)
    if diretoria_id:
        pedidos_pendentes_query = pedidos_pendentes_query.filter(Venda.diretoria_id == diretoria_id)
    pedidos_pendentes = pedidos_pendentes_query.filter(
        Pedido.status == PedidoStatusEnum.pendente
    ).scalar()

    return {
        "vendas_abertas": vendas_abertas,
        "vendas_finalizadas": vendas_finalizadas,
        "propostas_pendentes": propostas_pendentes,
        "pedidos_pendentes": pedidos_pendentes
    }
