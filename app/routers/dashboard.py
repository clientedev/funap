"""Router de Dashboard."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.auth import security
from app.models.usuario import Usuario
from app.services.dashboard import get_dashboard_metrics

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(security.get_current_active_user)
):
    diretoria_id = current_user.diretoria_id if current_user.perfil != "admin" else None
    
    metrics = get_dashboard_metrics(db, diretoria_id)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "metrics": metrics, "user": current_user}
    )
    
@router.get("/")
async def index():
    return RedirectResponse(url="/dashboard")
