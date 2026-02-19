"""Router de Diretorias."""
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.auth import security
from app.models.usuario import Usuario, PerfilEnum
from app.models.diretoria import Diretoria
from app.repositories.base import BaseRepository

router = APIRouter(prefix="/diretorias", tags=["diretorias"])
templates = Jinja2Templates(directory="app/templates")
repo = BaseRepository(Diretoria)

@router.get("")
async def list_diretorias(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    diretorias = repo.get_multi(db)
    return templates.TemplateResponse(
        "diretorias/list.html", 
        {"request": request, "diretorias": diretorias, "user": current_user}
    )

@router.get("/nova")
async def create_diretoria_form(
    request: Request,
    current_user: Usuario = Depends(security.get_current_active_user)
):
    if current_user.perfil != PerfilEnum.admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    return templates.TemplateResponse(
        "diretorias/form.html",
        {"request": request, "diretoria": None, "user": current_user}
    )

@router.post("/nova")
async def create_diretoria(
    nome: str = Form(...),
    descricao: str = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    if current_user.perfil != PerfilEnum.admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    repo.create(db, obj_in={"nome": nome, "descricao": descricao})
    return RedirectResponse(url="/diretorias", status_code=303)

@router.get("/{diretoria_id}/editar")
async def update_diretoria_form(
    diretoria_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    if current_user.perfil != PerfilEnum.admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    diretoria = repo.get(db, id=diretoria_id)
    return templates.TemplateResponse(
        "diretorias/form.html",
        {"request": request, "diretoria": diretoria, "user": current_user}
    )

@router.post("/{diretoria_id}/editar")
async def update_diretoria(
    diretoria_id: int,
    nome: str = Form(...),
    descricao: str = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    if current_user.perfil != PerfilEnum.admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    diretoria = repo.get(db, id=diretoria_id)
    repo.update(db, db_obj=diretoria, obj_in={"nome": nome, "descricao": descricao})
    return RedirectResponse(url="/diretorias", status_code=303)

@router.get("/{diretoria_id}/excluir")
async def delete_diretoria(
    diretoria_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    if current_user.perfil != PerfilEnum.admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    repo.remove(db, id=diretoria_id)
    return RedirectResponse(url="/diretorias", status_code=303)
