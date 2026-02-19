"""Service for Excel Import/Export utilities."""
import pandas as pd
import io
from typing import List, Dict, Any
from app.models.cliente import Cliente
from app.models.linha_produto import LinhaProduto

def generate_cliente_template() -> io.BytesIO:
    """Generates an Excel template for Clientes."""
    df = pd.DataFrame(columns=["nome", "cnpj_cpf", "email", "telefone", "endereco"])
    # Add dummy data
    df.loc[0] = ["Nome do Cliente Exemplo", "00.000.000/0001-00", "contato@cliente.com", "(11) 9999-9999", "Rua Exemplo, 123"]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Clientes")
    output.seek(0)
    return output

def generate_produto_template() -> io.BytesIO:
    """Generates an Excel template for Linhas de Produto."""
    df = pd.DataFrame(columns=["nome", "descricao"])
    # Add dummy data
    df.loc[0] = ["Nome da Linha de Produto", "Descrição breve do produto"]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Produtos")
    output.seek(0)
    return output

def parse_excel_import(file_content: bytes) -> List[Dict[str, Any]]:
    """Parses an uploaded Excel file into a list of dictionaries."""
    df = pd.read_excel(io.BytesIO(file_content))
    return df.to_dict(orient="records")
