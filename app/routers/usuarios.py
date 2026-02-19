"""Router de Usuários."""
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.auth import security
from app.models.usuario import Usuario, PerfilEnum
from app.models.diretoria import Diretoria
from app.repositories.base import BaseRepository

router = APIRouter(prefix="/usuarios", tags=["usuarios"])
templates = Jinja2Templates(directory="app/templates")
repo = BaseRepository(Usuario)

@router.get("")
async def list_usuarios(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    if current_user.perfil != PerfilEnum.admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    query = db.query(Usuario)
    if current_user.diretoria_id:
        query = query.filter(Usuario.diretoria_id == current_user.diretoria_id)
        
    usuarios = query.all()
    return templates.TemplateResponse(
        "usuarios/list.html",
        {"request": request, "usuarios": usuarios, "user": current_user}
    )

@router.get("/novo")
async def create_user_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    if current_user.perfil != PerfilEnum.admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    diretorias = db.query(Diretoria).all()
    return templates.TemplateResponse(
        "usuarios/form.html",
        {"request": request, "usuario": None, "diretorias": diretorias, "user": current_user}
    )

@router.post("/novo")
async def create_user(
    nome: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    perfil: str = Form(...),
    diretoria_id: int = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    if current_user.perfil != PerfilEnum.admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Se o admin pertence a uma diretoria, ele só pode criar usuários para ela
    if current_user.diretoria_id:
        diretoria_id = current_user.diretoria_id
        
    repo.create(db, obj_in={
        "nome": nome,
        "email": email,
        "senha_hash": security.get_password_hash(password),
        "perfil": perfil.lower(),
        "diretoria_id": diretoria_id,
        "ativo": True
    })
    return RedirectResponse(url="/usuarios", status_code=303)

@router.get("/{user_id}/editar")
async def update_user_form(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    if current_user.perfil != PerfilEnum.admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    usuario = repo.get(db, id=user_id)
    diretorias = db.query(Diretoria).all()
    return templates.TemplateResponse(
        "usuarios/form.html",
        {"request": request, "usuario": usuario, "diretorias": diretorias, "user": current_user}
    )

@router.post("/{user_id}/editar")
async def update_user(
    user_id: int,
    nome: str = Form(...),
    email: str = Form(...),
    perfil: str = Form(...),
    diretoria_id: int = Form(None),
    ativo: str = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    if current_user.perfil != PerfilEnum.admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
        
    usuario = repo.get(db, id=user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    # Restrição de diretoria para edição
    if current_user.diretoria_id and usuario.diretoria_id != current_user.diretoria_id:
        raise HTTPException(status_code=403, detail="Acesso negado: Usuário de outra diretoria")
    
    # Se o admin pertence a uma diretoria, ele não pode mudar a diretoria do usuário para outra
    if current_user.diretoria_id:
        diretoria_id = current_user.diretoria_id

    repo.update(db, db_obj=usuario, obj_in={
        "nome": nome,
        "email": email,
        "perfil": perfil.lower(),
        "diretoria_id": diretoria_id,
        "ativo": True if ativo == "on" else False
    })
    return RedirectResponse(url="/usuarios", status_code=303)

@router.get("/{user_id}/excluir")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    if current_user.perfil != PerfilEnum.admin:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    usuario = repo.get(db, id=user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    if current_user.diretoria_id and usuario.diretoria_id != current_user.diretoria_id:
        raise HTTPException(status_code=403, detail="Acesso negado: Usuário de outra diretoria")

    repo.remove(db, id=user_id)
    return RedirectResponse(url="/usuarios", status_code=303)
