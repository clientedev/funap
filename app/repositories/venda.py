"""Repositório de Vendas com filtros customizados."""
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.venda import Venda
from app.models.cliente import Cliente
from app.models.proposta import Proposta
from app.models.pedido import Pedido
from app.models.nota_fiscal import NotaFiscal
from app.repositories.base import BaseRepository


class VendaRepository(BaseRepository[Venda]):
    def __init__(self):
        super().__init__(Venda)

    def get_by_filters(
        self,
        db: Session,
        diretoria_id: Optional[int] = None,
        cliente_nome: Optional[str] = None,
        proposta_numero: Optional[str] = None,
        proposta_status: Optional[str] = None,
        pedido_numero: Optional[str] = None,
        pedido_status: Optional[str] = None,
        nota_fiscal_numero: Optional[str] = None,
        linha_produto_id: Optional[int] = None,
        venda_status: Optional[str] = None,
        modalidade: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Venda]:
        query = db.query(Venda).options(
            joinedload(Venda.cliente),
            joinedload(Venda.diretoria),
            joinedload(Venda.linha_produto),
            selectinload(Venda.propostas),
            selectinload(Venda.pedidos),
            selectinload(Venda.notas_fiscais)
        )

        # Filtro de Diretoria (sempre aplicado se presente)
        if diretoria_id:
            query = query.filter(Venda.diretoria_id == diretoria_id)

        # Filtros simples da entidade Venda
        if venda_status:
            query = query.filter(Venda.status == venda_status)

        if linha_produto_id:
            query = query.filter(Venda.linha_produto_id == linha_produto_id)

        if modalidade:
            query = query.filter(Venda.modalidade == modalidade)

        # Busca Geral (campo 'q') - Pesquisa em OS, Objeto e Nome do Cliente
        if cliente_nome:
            # cliente_nome aqui representa o parâmetro 'q' passado do router
            query = query.outerjoin(Venda.cliente).filter(
                or_(
                    Venda.numero.ilike(f"%{cliente_nome}%"),
                    Venda.objeto.ilike(f"%{cliente_nome}%"),
                    Cliente.nome.ilike(f"%{cliente_nome}%")
                )
            )

        # Filtros específicos do Ciclo de Vida (usando outerjoin para não excluir vendas sem vínculos)
        if proposta_numero or proposta_status:
            query = query.outerjoin(Venda.propostas)
            if proposta_numero:
                query = query.filter(Proposta.numero.ilike(f"%{proposta_numero}%"))
            if proposta_status:
                query = query.filter(Proposta.status == proposta_status)

        if pedido_numero or pedido_status:
            query = query.outerjoin(Venda.pedidos)
            if pedido_numero:
                query = query.filter(Pedido.numero.ilike(f"%{pedido_numero}%"))
            if pedido_status:
                query = query.filter(Pedido.status == pedido_status)

        if nota_fiscal_numero:
            query = query.outerjoin(Venda.notas_fiscais).filter(NotaFiscal.numero.ilike(f"%{nota_fiscal_numero}%"))

        # Distinct para evitar duplicatas devido aos joins
        return query.distinct().offset(skip).limit(limit).all()

venda_repo = VendaRepository()
