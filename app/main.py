# SISCONT - Deploy V34 (STABLE LOCKDOWN) - 19/02/2026 17:40
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Oid fix is now handled in database.py via connection listeners
    yield

app = FastAPI(title="SisCont", version="1.0.0", lifespan=lifespan)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Restaura o comportamento de redirecionamento para o usuário final
    if exc.status_code == 401: return RedirectResponse(url="/login")
    if exc.status_code == 403: return RedirectResponse(url="/dashboard")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    # Mantemos o log detalhado no 500 para debug interno se algo novo quebrar
    print(f"CRITICAL ERROR: {traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor", "error": str(exc)})

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(diretorias.router)
app.include_router(usuarios.router)
app.include_router(vendas.router)
app.include_router(clientes.router)
app.include_router(linhas_produto.router)
