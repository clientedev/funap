"""Router de Clientes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
import io

from app.database import get_db
from app.auth import security
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.repositories.base import BaseRepository
from app.services.excel_utils import generate_cliente_template, parse_excel_import

router = APIRouter(prefix="/clientes", tags=["clientes"])
templates = Jinja2Templates(directory="app/templates")
cliente_repo = BaseRepository(Cliente)

@router.get("")
async def list_clientes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    clientes = cliente_repo.get_multi(db)
    return templates.TemplateResponse(
        "clientes/list.html",
        {"request": request, "clientes": clientes, "user": current_user}
    )

@router.get("/novo")
async def create_cliente_form(
    request: Request,
    current_user: Usuario = Depends(security.get_current_active_user)
):
    return templates.TemplateResponse(
        "clientes/form.html",
        {"request": request, "cliente": None, "user": current_user}
    )

@router.post("/novo")
async def create_cliente(
    nome: str = Form(...),
    cnpj_cpf: str = Form(...),
    email: str = Form(None),
    telefone: str = Form(None),
    endereco: str = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    cliente_repo.create(db, obj_in={
        "nome": nome,
        "cnpj_cpf": cnpj_cpf,
        "email": email,
        "telefone": telefone,
        "endereco": endereco
    })
    return RedirectResponse(url="/clientes", status_code=303)

@router.get("/{cliente_id}/editar")
async def update_cliente_form(
    cliente_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    cliente = cliente_repo.get(db, id=cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return templates.TemplateResponse(
        "clientes/form.html",
        {"request": request, "cliente": cliente, "user": current_user}
    )

@router.post("/{cliente_id}/editar")
async def update_cliente(
    cliente_id: int,
    nome: str = Form(...),
    cnpj_cpf: str = Form(...),
    email: str = Form(None),
    telefone: str = Form(None),
    endereco: str = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    cliente = cliente_repo.get(db, id=cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
    cliente_repo.update(db, db_obj=cliente, obj_in={
        "nome": nome,
        "cnpj_cpf": cnpj_cpf,
        "email": email,
        "telefone": telefone,
        "endereco": endereco
    })
    return RedirectResponse(url="/clientes", status_code=303)

@router.get("/{cliente_id}/excluir")
async def delete_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    cliente_repo.remove(db, id=cliente_id)
    return RedirectResponse(url="/clientes", status_code=303)

@router.get("/template")
async def download_template(
    current_user: Usuario = Depends(security.get_current_active_user)
):
    excel_file = generate_cliente_template()
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=modelo_clientes.xlsx"}
    )

@router.post("/importar")
async def import_clientes(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    content = await file.read()
    data = parse_excel_import(content)
    for row in data:
        # Simple validation/creation
        if "nome" in row and "cnpj_cpf" in row:
            cliente_repo.create(db, obj_in=row)
    return RedirectResponse(url="/clientes", status_code=303)
