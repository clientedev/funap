"""Serviço de Dashboard para Indicadores."""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.venda import Venda, VendaStatusEnum
from app.models.proposta import Proposta, PropostaStatusEnum
from app.models.pedido import Pedido, PedidoStatusEnum
from app.models.nota_fiscal import NotaFiscal, NFEStatusEntregaEnum

from app.models.linha_produto import LinhaProduto

def get_dashboard_metrics(db: Session, diretoria_id: int | None = None):
    """
    Retorna métricas consolidadas e dados para gráficos.
    """
    filters = []
    if diretoria_id:
        filters.append(Venda.diretoria_id == diretoria_id)

    # 1. Métricas de Resumo (Cards)
    vendas_andamento = db.query(func.count(Venda.id)).filter(
        Venda.status == VendaStatusEnum.em_andamento, *filters
    ).scalar()

    vendas_finalizadas = db.query(func.count(Venda.id)).filter(
        Venda.status == VendaStatusEnum.finalizada, *filters
    ).scalar()

    vendas_canceladas = db.query(func.count(Venda.id)).filter(
        Venda.status == VendaStatusEnum.cancelada, *filters
    ).scalar()

    propostas_pendentes_query = db.query(func.count(Proposta.id)).join(Venda)
    if diretoria_id:
        propostas_pendentes_query = propostas_pendentes_query.filter(Venda.diretoria_id == diretoria_id)
    propostas_pendentes = propostas_pendentes_query.filter(
        Proposta.status == PropostaStatusEnum.pendente
    ).scalar()

    pedidos_pendentes_query = db.query(func.count(Pedido.id)).join(Venda)
    if diretoria_id:
        pedidos_pendentes_query = pedidos_pendentes_query.filter(Venda.diretoria_id == diretoria_id)
    pedidos_pendentes = pedidos_pendentes_query.filter(
        Pedido.status == PedidoStatusEnum.pendente
    ).scalar()
    
    notas_parciais_query = db.query(func.count(NotaFiscal.id)).join(Venda)
    if diretoria_id:
        notas_parciais_query = notas_parciais_query.filter(Venda.diretoria_id == diretoria_id)
    notas_parciais = notas_parciais_query.filter(
        NotaFiscal.status_entrega == NFEStatusEntregaEnum.parcial
    ).scalar()

    # 2. Distribuição por Linha de Produto (Gráfico de Rosca)
    dist_linha = db.query(
        LinhaProduto.nome,
        func.count(Venda.id)
    ).join(Venda).filter(*filters).group_by(LinhaProduto.nome).all()
    
    labels_linha = [r[0] for r in dist_linha]
    values_linha = [r[1] for r in dist_linha]

    # 3. Evolução de Vendas (Gráfico de Linha - Últimos 6 meses)
    # Nota: Em SQLite/PostgreSQL a extração de data muda, mas vamos usar func.strftime/func.to_char
    # Como o alvo é Railway (Postgres):
    evolucao_query = db.query(
        func.to_char(Venda.created_at, 'YYYY-MM').label('mes'),
        func.count(Venda.id)
    ).filter(*filters).group_by('mes').order_by('mes').limit(6).all()

    # Caso seja SQLite para teste local:
    if "sqlite" in str(db.get_bind().url):
        evolucao_query = db.query(
            func.strftime('%Y-%m', Venda.created_at).label('mes'),
            func.count(Venda.id)
        ).filter(*filters).group_by('mes').order_by('mes').limit(6).all()

    labels_evolucao = [r[0] for r in evolucao_query]
    values_evolucao = [r[1] for r in evolucao_query]

    # 4. Total de Vendas (Geral)
    total_vendas = db.query(func.count(Venda.id)).filter(*filters).scalar()

    return {
        "resumo": {
            "vendas_andamento": vendas_andamento,
            "vendas_finalizadas": vendas_finalizadas,
            "vendas_canceladas": vendas_canceladas,
            "propostas_pendentes": propostas_pendentes,
            "pedidos_pendentes": pedidos_pendentes,
            "notas_parciais": notas_parciais,
            "total_vendas": total_vendas
        },
        "graficos": {
            "linha_produto": {"labels": labels_linha, "values": values_linha},
            "evolucao": {"labels": labels_evolucao, "values": values_evolucao}
        }
    }
