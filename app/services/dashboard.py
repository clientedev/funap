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

    # Vendas em Andamento (Tudo que não é Finalizada ou Cancelada)
    vendas_andamento = db.query(func.count(Venda.id)).filter(
        Venda.status.notin_([VendaStatusEnum.finalizada, VendaStatusEnum.cancelada]), 
        *filters
    ).scalar()

    # Vendas Finalizadas
    vendas_finalizadas = db.query(func.count(Venda.id)).filter(
        Venda.status == VendaStatusEnum.finalizada, *filters
    ).scalar()

    # Propostas Pendentes
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
    
    # Notas com Entrega Parcial
    notas_parciais_query = db.query(func.count(NotaFiscal.id)).join(Venda)
    if diretoria_id:
        notas_parciais_query = notas_parciais_query.filter(Venda.diretoria_id == diretoria_id)
    notas_parciais = notas_parciais_query.filter(
        NotaFiscal.status_entrega == NFEStatusEntregaEnum.parcial
    ).scalar()

    return {
        "vendas_andamento": vendas_andamento,
        "vendas_finalizadas": vendas_finalizadas,
        "propostas_pendentes": propostas_pendentes,
        "pedidos_pendentes": pedidos_pendentes,
        "notas_parciais": notas_parciais
    }
