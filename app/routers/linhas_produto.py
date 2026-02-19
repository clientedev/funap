"""Router de Linhas de Produto."""
from fastapi import APIRouter, Depends, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
import io

from app.database import get_db
from app.auth import security
from app.models.usuario import Usuario
from app.models.linha_produto import LinhaProduto
from app.repositories.base import BaseRepository
from app.services.excel_utils import generate_produto_template, parse_excel_import

router = APIRouter(prefix="/linhas-produto", tags=["linhas-produto"])
templates = Jinja2Templates(directory="app/templates")
linha_repo = BaseRepository(LinhaProduto)

@router.get("")
async def list_linhas(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    linhas = linha_repo.get_multi(db)
    return templates.TemplateResponse(
        "linhas_produto/list.html",
        {"request": request, "linhas": linhas, "user": current_user}
    )

@router.get("/novo")
async def create_linha_form(
    request: Request,
    current_user: Usuario = Depends(security.get_current_active_user)
):
    return templates.TemplateResponse(
        "linhas_produto/form.html",
        {"request": request, "linha": None, "user": current_user}
    )

@router.post("/novo")
async def create_linha(
    nome: str = Form(...),
    descricao: str = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    linha_repo.create(db, obj_in={"nome": nome, "descricao": descricao})
    return RedirectResponse(url="/linhas-produto", status_code=303)

@router.get("/{linha_id}/editar")
async def update_linha_form(
    linha_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    linha = linha_repo.get(db, id=linha_id)
    if not linha:
        raise HTTPException(status_code=404, detail="Linha não encontrada")
    return templates.TemplateResponse(
        "linhas_produto/form.html",
        {"request": request, "linha": linha, "user": current_user}
    )

@router.post("/{linha_id}/editar")
async def update_linha(
    linha_id: int,
    nome: str = Form(...),
    descricao: str = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    linha = linha_repo.get(db, id=linha_id)
    if not linha:
        raise HTTPException(status_code=404, detail="Linha não encontrada")
    linha_repo.update(db, db_obj=linha, obj_in={"nome": nome, "descricao": descricao})
    return RedirectResponse(url="/linhas-produto", status_code=303)

@router.get("/{linha_id}/excluir")
async def delete_linha(
    linha_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    linha_repo.remove(db, id=linha_id)
    return RedirectResponse(url="/linhas-produto", status_code=303)

@router.get("/template")
async def download_template(
    current_user: Usuario = Depends(security.get_current_active_user)
):
    excel_file = generate_produto_template()
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=modelo_produtos.xlsx"}
    )

@router.post("/importar")
async def import_produtos(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    content = await file.read()
    data = parse_excel_import(content)
    for row in data:
        if "nome" in row:
            linha_repo.create(db, obj_in=row)
    return RedirectResponse(url="/linhas-produto", status_code=303)
