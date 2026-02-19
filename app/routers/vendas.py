"""Router de Vendas."""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, Form, Path, UploadFile, File
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.auth import security
from app.models.usuario import Usuario
from app.models.venda import Venda, ModalidadeEnum
from app.models.cliente import Cliente
from app.models.linha_produto import LinhaProduto
from app.models.proposta import Proposta
from app.models.pedido import Pedido
from app.models.empenho import Empenho
from app.models.contrato import Contrato
from app.models.nota_fiscal import NotaFiscal
from app.models.solicitacao_custo import SolicitacaoCusto
from app.repositories.venda import venda_repo
from app.services.excel_export import export_vendas_to_excel

router = APIRouter(prefix="/vendas", tags=["vendas"])
templates = Jinja2Templates(directory="app/templates")

@router.get("")
async def list_vendas(
    request: Request,
    q: Optional[str] = None,
    proposta_num: Optional[str] = None,
    pedido_num: Optional[str] = None,
    nfe_num: Optional[str] = None,
    status: Optional[str] = None,
    modalidade: Optional[str] = None,
    proposta_status: Optional[str] = None,
    pedido_status: Optional[str] = None,
    linha_produto_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    # Removido filtro de diretoria para visualização global
    vendas = venda_repo.get_by_filters(
        db, 
        diretoria_id=None,
        cliente_nome=q,
        proposta_numero=proposta_num,
        pedido_numero=pedido_num,
        nota_fiscal_numero=nfe_num,
        venda_status=status,
        modalidade=modalidade,
        proposta_status=proposta_status,
        pedido_status=pedido_status,
        linha_produto_id=linha_produto_id
    )
    return templates.TemplateResponse(
        "vendas/list.html",
        {"request": request, "vendas": vendas, "user": current_user}
    )

@router.get("/nova")
async def create_venda_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    clientes = db.query(Cliente).all()
    linhas = db.query(LinhaProduto).all()
    return templates.TemplateResponse(
        "vendas/form.html",
        {"request": request, "clientes": clientes, "linhas": linhas, "user": current_user}
    )

@router.post("/nova")
async def create_venda(
    cliente_id: int = Form(...),
    linha_produto_id: int = Form(...),
    objeto: str = Form(...),
    modalidade: str = Form("VENDA"),
    processo_sei: str = Form(None),
    numero: str = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    venda = Venda(
        cliente_id=cliente_id,
        linha_produto_id=linha_produto_id,
        diretoria_id=current_user.diretoria_id or 1,
        criado_por_id=current_user.id,
        objeto=objeto,
        modalidade=modalidade.lower(),
        processo_sei=processo_sei,
        numero=numero or f"V-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        status="em_andamento"
    )
    db.add(venda)
    db.commit()
    db.refresh(venda)
    return RedirectResponse(url=f"/vendas/{venda.id}", status_code=303)

@router.get("/pesquisa")
async def pesquisa_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    linhas = db.query(LinhaProduto).all()
    return templates.TemplateResponse(
        "pesquisa.html", 
        {"request": request, "linhas": linhas, "user": current_user}
    )

@router.get("/{venda_id}")
async def view_venda(
    venda_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    return templates.TemplateResponse(
        "vendas/detail.html",
        {"request": request, "venda": venda, "user": current_user}
    )

# Adicionar Proposta
@router.post("/{venda_id}/solicitacao-custo")
async def create_solicitacao_custo(
    venda_id: int,
    data_solicitacao: str = Form(None),
    data_resposta: str = Form(None),
    descricao: str = Form(None),
    valor_estimado: float = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    venda = venda_repo.get(db, id=venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    
    sc = SolicitacaoCusto(
        venda_id=venda_id,
        data_solicitacao=datetime.strptime(data_solicitacao, "%Y-%m-%d").date() if data_solicitacao else None,
        data_resposta=datetime.strptime(data_resposta, "%Y-%m-%d").date() if data_resposta else None,
        descricao=descricao,
        valor_estimado=valor_estimado,
        status="pendente"
    )
    db.add(sc)
    
    # Atualiza status da venda
    venda.status = "aguardando_proposta"
    
    db.commit()
    return RedirectResponse(url=f"/vendas/{venda_id}", status_code=303)

# Adicionar Proposta
@router.post("/{venda_id}/proposta")
async def create_proposta(
    venda_id: int,
    numero: str = Form(...),
    revisao: str = Form(None),
    valor: float = Form(...),
    data_emissao: str = Form(...),
    data_vencimento: str = Form(...),
    status: str = Form("pendente"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    venda = venda_repo.get(db, id=venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    
    p = Proposta(
        venda_id=venda_id,
        numero=numero,
        revisao=revisao,
        valor=valor,
        data_emissao=datetime.strptime(data_emissao, "%Y-%m-%d").date(),
        data_vencimento=datetime.strptime(data_vencimento, "%Y-%m-%d").date(),
        status=status.lower()
    )
    db.add(p)
    
    # Se a proposta for aprovada, atualiza status da venda
    if status.lower() == "aprovada":
        venda.status = "aguardando_empenho"
    
    db.commit()
    return RedirectResponse(url=f"/vendas/{venda_id}", status_code=303)

# Adicionar Contrato
@router.post("/{venda_id}/contrato")
async def create_contrato(
    venda_id: int,
    numero: str = Form(...),
    data_envio_sei: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    from app.models.contrato import Contrato
    venda = venda_repo.get(db, id=venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    
    c = Contrato(
        venda_id=venda_id,
        numero=numero,
        data_envio_sei_contratos=datetime.strptime(data_envio_sei, "%Y-%m-%d").date(),
        status="ativo"
    )
    db.add(c)
    db.commit()
    return RedirectResponse(url=f"/vendas/{venda_id}", status_code=303)

# Adicionar Empenho
@router.post("/{venda_id}/empenho")
async def create_empenho(
    venda_id: int,
    numero: str = Form(...),
    data_recebimento: str = Form(...),
    prazo_entrega: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    from app.models.empenho import Empenho
    venda = venda_repo.get(db, id=venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    
    e = Empenho(
        venda_id=venda_id,
        numero=numero,
        data_recebimento=datetime.strptime(data_recebimento, "%Y-%m-%d").date(),
        prazo_entrega=datetime.strptime(prazo_entrega, "%Y-%m-%d").date(),
        status="pendente"
    )
    db.add(e)
    
    # Atualiza status da venda
    if venda.status == "aguardando_empenho":
        venda.status = "faturado"
    
    db.commit()
    return RedirectResponse(url=f"/vendas/{venda_id}", status_code=303)

# Adicionar Pedido
@router.post("/{venda_id}/pedido")
async def create_pedido(
    venda_id: int,
    numero: str = Form(...),
    prazo_entrega: str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    venda = venda_repo.get(db, id=venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    
    p = Pedido(
        venda_id=venda_id,
        numero=numero,
        prazo_entrega=datetime.strptime(prazo_entrega, "%Y-%m-%d").date(),
        status=status
    )
    db.add(p)
    
    # Atualiza status da venda
    if venda.status == "faturado" or venda.status == "aguardando_empenho":
        venda.status = "faturado"
    
    db.commit()
    return RedirectResponse(url=f"/vendas/{venda_id}", status_code=303)

@router.post("/{venda_id}/nota-fiscal")
async def create_nota_fiscal(
    venda_id: int,
    numero: str = Form(...),
    data_emissao: str = Form(...),
    valor: float = Form(...),
    status_entrega: str = Form(...),
    arquivo_nf: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    venda = venda_repo.get(db, id=venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    
    # Processar arquivo se enviado
    nome_arquivo = None
    if arquivo_nf and arquivo_nf.filename:
        import os
        import uuid
        upload_dir = "app/static/uploads/nfs"
        os.makedirs(upload_dir, exist_ok=True)
        ext = os.path.splitext(arquivo_nf.filename)[1]
        nome_arquivo = f"nf_{uuid.uuid4()}{ext}"
        filepath = os.path.join(upload_dir, nome_arquivo)
        with open(filepath, "wb") as f:
            f.write(await arquivo_nf.read())
    
    nf = NotaFiscal(
        venda_id=venda_id,
        numero=numero,
        data_emissao=datetime.strptime(data_emissao, "%Y-%m-%d").date(),
        valor=valor,
        status_entrega=status_entrega.lower(),
        documento_pdf=nome_arquivo
    )
    db.add(nf)
    
    # Se ainda não estiver faturada ou finalizada, marca como faturado
    if venda.status not in ["faturado", "finalizada"]:
        venda.status = "faturado"
        
    db.commit()
    return RedirectResponse(url=f"/vendas/{venda_id}", status_code=303)

@router.post("/{venda_id}/editar")
async def update_venda(
    venda_id: int,
    cliente_id: int = Form(...),
    linha_produto_id: int = Form(...),
    objeto: str = Form(...),
    modalidade: str = Form(...),
    processo_sei: str = Form(None),
    status_venda: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    venda = venda_repo.get(db, id=venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    
    status_map = {
        "ABERTA": "em_andamento",
        "EM_ANDAMENTO": "em_andamento",
        "FINALIZADA": "finalizada",
        "CANCELADA": "cancelada"
    }
    
    update_data = {
        "cliente_id": cliente_id,
        "linha_produto_id": linha_produto_id,
        "objeto": objeto,
        "modalidade": modalidade.lower() if modalidade else "venda",
        "processo_sei": processo_sei,
        "status": status_map.get(status_venda.upper(), "em_andamento")
    }
    venda_repo.update(db, db_obj=venda, obj_in=update_data)
    return RedirectResponse(url=f"/vendas/{venda_id}", status_code=303)

@router.get("/{venda_id}/excluir")
async def delete_venda(
    venda_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    venda = venda_repo.get(db, id=venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    
    venda_repo.remove(db, id=venda_id)
    return RedirectResponse(url="/vendas", status_code=303)

@router.get("/exportar")
async def export_vendas_route(
    q: Optional[str] = None,
    proposta_num: Optional[str] = None,
    pedido_num: Optional[str] = None,
    nfe_num: Optional[str] = None,
    status: Optional[str] = None,
    modalidade: Optional[str] = None,
    proposta_status: Optional[str] = None,
    pedido_status: Optional[str] = None,
    linha_produto_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    # Removido filtro de diretoria para exportação global
    vendas = venda_repo.get_by_filters(
        db, 
        diretoria_id=None, 
        cliente_nome=q, 
        proposta_numero=proposta_num,
        pedido_numero=pedido_num,
        nota_fiscal_numero=nfe_num,
        venda_status=status,
        modalidade=modalidade,
        proposta_status=proposta_status,
        pedido_status=pedido_status,
        linha_produto_id=linha_produto_id
    )
    excel_file = export_vendas_to_excel(vendas, current_user.nome)
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=siscont_vendas.xlsx"}
    )

# --- Rotas de Exclusão de Itens do Ciclo de Vida ---

@router.get("/{venda_id}/solicitacao-custo/{item_id}/excluir")
async def delete_solicitacao(venda_id: int, item_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(security.get_current_active_user)):
    venda = venda_repo.get(db, id=venda_id)
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    item = db.query(SolicitacaoCusto).filter(SolicitacaoCusto.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url=f"/vendas/{venda_id}", status_code=303)

@router.get("/{venda_id}/proposta/{item_id}/excluir")
async def delete_proposta(venda_id: int, item_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(security.get_current_active_user)):
    venda = venda_repo.get(db, id=venda_id)
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    item = db.query(Proposta).filter(Proposta.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url=f"/vendas/{venda_id}", status_code=303)

@router.get("/{venda_id}/contrato/{item_id}/excluir")
async def delete_contrato(venda_id: int, item_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(security.get_current_active_user)):
    venda = venda_repo.get(db, id=venda_id)
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    item = db.query(Contrato).filter(Contrato.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url=f"/vendas/{venda_id}", status_code=303)

@router.get("/{venda_id}/empenho/{item_id}/excluir")
async def delete_empenho(venda_id: int, item_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(security.get_current_active_user)):
    venda = venda_repo.get(db, id=venda_id)
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    item = db.query(Empenho).filter(Empenho.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url=f"/vendas/{venda_id}", status_code=303)

@router.get("/{venda_id}/pedido/{item_id}/excluir")
async def delete_pedido(venda_id: int, item_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(security.get_current_active_user)):
    venda = venda_repo.get(db, id=venda_id)
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    item = db.query(Pedido).filter(Pedido.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url=f"/vendas/{venda_id}", status_code=303)

@router.get("/{venda_id}/nota-fiscal/{item_id}/excluir")
async def delete_nf(venda_id: int, item_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(security.get_current_active_user)):
    venda = venda_repo.get(db, id=venda_id)
    security.check_permission(current_user, diretoria_id=venda.diretoria_id)
    item = db.query(NotaFiscal).filter(NotaFiscal.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url=f"/vendas/{venda_id}", status_code=303)
