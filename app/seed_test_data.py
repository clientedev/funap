"""Script para popular a base com dados de teste variados."""
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.usuario import Usuario, PerfilEnum
from app.models.diretoria import Diretoria
from app.models.cliente import Cliente
from app.models.linha_produto import LinhaProduto
from app.models.venda import Venda, VendaStatusEnum, ModalidadeEnum
from app.models.solicitacao_custo import SolicitacaoCusto
from app.models.proposta import Proposta, PropostaStatusEnum
from app.models.contrato import Contrato
from app.models.empenho import Empenho
from app.models.pedido import Pedido, PedidoStatusEnum
from app.models.nota_fiscal import NotaFiscal, NFEStatusEntregaEnum
from app.auth.security import get_password_hash

def seed_data():
    db = SessionLocal()
    try:
        # 0. Limpar tabelas (opcional, para garantir um estado limpo)
        # Ordem reversa para evitar problemas de FK
        db.query(NotaFiscal).delete()
        db.query(Pedido).delete()
        db.query(Empenho).delete()
        db.query(Contrato).delete()
        db.query(Proposta).delete()
        db.query(SolicitacaoCusto).delete()
        db.query(Venda).delete()
        db.query(LinhaProduto).delete()
        db.query(Cliente).delete()
        db.commit()
        print("Tabelas limpas para re-seeding.")

        # 1. Diretorias
        dicom = db.query(Diretoria).filter(Diretoria.nome == "DICOM").first()
        if not dicom:
            dicom = Diretoria(nome="DICOM", descricao="Diretoria Comercial")
            db.add(dicom)
        
        dipro = db.query(Diretoria).filter(Diretoria.nome == "DIPRO").first()
        if not dipro:
            dipro = Diretoria(nome="DIPRO", descricao="Diretoria de Produção")
            db.add(dipro)
        
        db.commit()
        db.refresh(dicom)
        db.refresh(dipro)

        # 2. Usuários
        user_dicom = db.query(Usuario).filter(Usuario.email == "comercial@funap.gov.br").first()
        if not user_dicom:
            user_dicom = Usuario(
                nome="Vendedor Comercial",
                email="comercial@funap.gov.br",
                senha_hash=get_password_hash("funap123"),
                perfil=PerfilEnum.usuario,
                diretoria_id=dicom.id
            )
            db.add(user_dicom)

        user_dipro = db.query(Usuario).filter(Usuario.email == "producao@funap.gov.br").first()
        if not user_dipro:
            user_dipro = Usuario(
                nome="Gestor de Produção",
                email="producao@funap.gov.br",
                senha_hash=get_password_hash("funap123"),
                perfil=PerfilEnum.usuario,
                diretoria_id=dipro.id
            )
            db.add(user_dipro)
        
        db.commit()
        db.refresh(user_dicom)
        db.refresh(user_dipro)

        # 3. Clientes
        clientes_data = [
            {"nome": "Secretaria da Administração Penitenciária (SAP)", "cnpj_cpf": "48.031.918/0001-24"},
            {"nome": "Prefeitura Municipal de São Paulo", "cnpj_cpf": "46.395.000/0001-39"},
            {"nome": "Tribunal de Justiça de São Paulo", "cnpj_cpf": "51.174.001/0001-93"},
        ]
        cleintes_objs = []
        for cdata in clientes_data:
            c = db.query(Cliente).filter(Cliente.cnpj_cpf == cdata["cnpj_cpf"]).first()
            if not c:
                c = Cliente(**cdata)
                db.add(c)
                db.commit()
                db.refresh(c)
            cleintes_objs.append(c)

        # 4. Linhas de Produto
        linhas_data = [
            {"nome": "Mobiliário para Escritório", "descricao": "Cadeiras, mesas e armários"},
            {"nome": "Confecção / Vestuário", "descricao": "Uniformes e vestuário hospitalar"},
            {"nome": "Metalurgia", "descricao": "Grades e estruturas metálicas"},
        ]
        linhas_objs = []
        for ldata in linhas_data:
            l = db.query(LinhaProduto).filter(LinhaProduto.nome == ldata["nome"]).first()
            if not l:
                l = LinhaProduto(**ldata)
                db.add(l)
                db.commit()
                db.refresh(l)
            linhas_objs.append(l)

        # 5. Vendas e Ciclos de Vida
        
        # Caso 1: Venda em andamento (com Proposta e Contrato)
        v1 = db.query(Venda).filter(Venda.numero == "OS-2026-001").first()
        if not v1:
            v1 = Venda(
                numero="OS-2026-001",
                processo_sei="001/2026-SAP",
                objeto="Fornecimento de 500 cadeiras de escritório modelo ergonômico",
                status=VendaStatusEnum.aberta,
                modalidade=ModalidadeEnum.venda,
                cliente_id=cleintes_objs[0].id,
                diretoria_id=dicom.id,
                linha_produto_id=linhas_objs[0].id,
                criado_por_id=user_dicom.id
            )
            db.add(v1)
            db.commit()
            db.refresh(v1)
            
            # Solicitação de Custo
            db.add(SolicitacaoCusto(
                venda_id=v1.id, 
                data_solicitacao=date.today() - timedelta(days=10),
                data_resposta=date.today() - timedelta(days=8),
                status="concluida",
                descricao="Solicito custo para 500 cadeiras"
            ))
            
            # Proposta
            db.add(Proposta(
                venda_id=v1.id,
                numero="PROP-001/2026",
                revisao="0",
                valor=125000.00,
                data_emissao=date.today() - timedelta(days=7),
                status=PropostaStatusEnum.aprovada
            ))
            
            # Contrato
            db.add(Contrato(
                venda_id=v1.id,
                numero="CONT-001/2026",
                data_envio_sei_contratos=date.today() - timedelta(days=5),
                status="ativo"
            ))
            db.commit()

        # Caso 2: Venda Finalizada (Fluxo completo)
        v2 = db.query(Venda).filter(Venda.numero == "OS-2026-002").first()
        if not v2:
            v2 = Venda(
                numero="OS-2026-002",
                processo_sei="002/2026-PMSP",
                objeto="Uniformes para guarda civil municipal",
                status=VendaStatusEnum.finalizada,
                modalidade=ModalidadeEnum.licitacao,
                cliente_id=cleintes_objs[1].id,
                diretoria_id=dipro.id,
                linha_produto_id=linhas_objs[1].id,
                criado_por_id=user_dipro.id
            )
            db.add(v2)
            db.commit()
            db.refresh(v2)
            
            # Proposta
            db.add(Proposta(
                venda_id=v2.id,
                numero="PROP-002/2026",
                valor=450000.00,
                data_emissao=date.today() - timedelta(days=30),
                status=PropostaStatusEnum.aprovada
            ))
            
            # Empenho
            db.add(Empenho(
                venda_id=v2.id,
                numero="EMP-001/2026",
                data_recebimento=date.today() - timedelta(days=20),
                prazo_entrega=date.today() + timedelta(days=10),
                valor=450000.00,
                status="empenhado"
            ))
            
            # Pedido
            db.add(Pedido(
                venda_id=v2.id,
                numero="PED-001/2026",
                prazo_entrega=date.today() + timedelta(days=10),
                status=PedidoStatusEnum.finalizado
            ))
            
            # Nota Fiscal
            db.add(NotaFiscal(
                venda_id=v2.id,
                numero="NF-12345",
                data_emissao=date.today() - timedelta(days=2),
                valor=450000.00,
                status_entrega=NFEStatusEntregaEnum.total
            ))
            db.commit()

        print("Dados de teste semeados com sucesso!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
