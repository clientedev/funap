"""Serviço de Exportação para Excel."""
from datetime import datetime
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from typing import List
from app.models.venda import Venda

def export_vendas_to_excel(vendas: List[Venda], user_nome: str) -> BytesIO:
    import pandas as pd
    import io
    
    data = []
    for v in vendas:
        # Get latest records for each phase
        proposta = v.propostas[-1] if v.propostas else None
        pedido = v.pedidos[-1] if v.pedidos else None
        nf = v.notas_fiscais[-1] if v.notas_fiscais else None
        
        row = {
            "ID Venda": v.id,
            "Número OS/Ref": v.numero,
            "Processo SEI": v.processo_sei,
            "Objeto": v.objeto,
            "Modalidade": v.modalidade.value if hasattr(v.modalidade, 'value') else v.modalidade,
            "Cliente": v.cliente.nome if v.cliente else "N/A",
            "Linha de Produto": v.linha_produto.nome if v.linha_produto else "N/A",
            "Diretoria": v.diretoria.nome if v.diretoria else "N/A",
            "Status Venda": v.status.value if hasattr(v.status, 'value') else v.status,
            "Proposta": proposta.numero if proposta else "N/A",
            "Vencimento Proposta": (proposta.data_vencimento.strftime("%d/%m/%Y") if proposta.data_vencimento else "N/A") if proposta else "N/A",
            "Status Proposta": (proposta.status.value if hasattr(proposta.status, 'value') else proposta.status) if proposta else "N/A",
            "Pedido": pedido.numero if pedido else "N/A",
            "Status Pedido": (pedido.status.value if hasattr(pedido.status, 'value') else pedido.status) if pedido else "N/A",
            "Nota Fiscal": nf.numero if nf else "N/A",
            "Data Emissão NF": nf.data_emissao.strftime("%d/%m/%Y") if nf and nf.data_emissao else "N/A",
            "Status Entrega": (nf.status_entrega.value if hasattr(nf.status_entrega, 'value') else nf.status_entrega) if nf else "N/A",
            "Data Criação": v.created_at.strftime("%d/%m/%Y %H:%M") if v.created_at else "N/A"
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="SISCONT_Vendas")
    
    output.seek(0)
    return output
