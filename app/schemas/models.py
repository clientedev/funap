"""Pydantic schemas for data validation."""
from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional, List
from app.models.venda import VendaStatusEnum
from app.models.proposta import PropostaStatusEnum
from app.models.pedido import PedidoStatusEnum
from app.models.nota_fiscal import NFEStatusEntregaEnum
from app.models.solicitacao_custo import SolicitacaoCustoStatusEnum

class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class ClienteSchema(SchemaBase):
    id: Optional[int] = None
    nome: str
    cnpj_cpf: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None

class LinhaProdutoSchema(SchemaBase):
    id: Optional[int] = None
    nome: str
    descricao: Optional[str] = None

class SolicitacaoCustoSchema(SchemaBase):
    id: Optional[int] = None
    venda_id: int
    data_solicitacao: Optional[date] = None
    data_resposta: Optional[date] = None
    status: SolicitacaoCustoStatusEnum = SolicitacaoCustoStatusEnum.pendente
    descricao: Optional[str] = None

class PropostaSchema(SchemaBase):
    id: Optional[int] = None
    venda_id: int
    numero: str
    revisao: Optional[str] = None
    data_emissao: Optional[date] = None
    data_validade: Optional[date] = None
    valor: Optional[float] = None
    status: PropostaStatusEnum = PropostaStatusEnum.pendente

class ContratoSchema(SchemaBase):
    id: Optional[int] = None
    venda_id: int
    numero: str
    data_envio_sei_contratos: Optional[date] = None
    data_assinatura: Optional[date] = None
    data_vigencia: Optional[date] = None
    valor: Optional[float] = None

class EmpenhoSchema(SchemaBase):
    id: Optional[int] = None
    venda_id: int
    numero: str
    data_recebimento: Optional[date] = None
    prazo_entrega: Optional[date] = None
    valor: Optional[float] = None

class PedidoSchema(SchemaBase):
    id: Optional[int] = None
    venda_id: int
    numero: str
    prazo_entrega: Optional[date] = None
    status: PedidoStatusEnum = PedidoStatusEnum.pendente

class NotaFiscalSchema(SchemaBase):
    id: Optional[int] = None
    venda_id: int
    numero: str
    data_emissao: Optional[date] = None
    valor: Optional[float] = None
    status_entrega: NFEStatusEntregaEnum = NFEStatusEntregaEnum.pendente

class VendaSchema(SchemaBase):
    id: Optional[int] = None
    numero: str
    processo_sei: Optional[str] = None
    cliente_id: int
    linha_produto_id: Optional[int] = None
    diretoria_id: int
    status: VendaStatusEnum = VendaStatusEnum.aberta
    objeto: Optional[str] = None
    created_at: datetime
    
    solicitacoes_custo: List[SolicitacaoCustoSchema] = []
    propostas: List[PropostaSchema] = []
    contratos: List[ContratoSchema] = []
    empenhos: List[EmpenhoSchema] = []
    pedidos: List[PedidoSchema] = []
    notas_fiscais: List[NotaFiscalSchema] = []
