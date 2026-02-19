from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto

app = FastAPI(title="SisCont", version="1.0.0")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    return RedirectResponse(url="/login") 

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(diretorias.router)
app.include_router(usuarios.router)
app.include_router(vendas.router)
app.include_router(clientes.router)
app.include_router(linhas_produto.router)

@app.get("/")
def root():
    return RedirectResponse(url="/dashboard")

# Exception handler para redirecionar para login se não autenticado (opcional, melhor tratar no middleware ou deps)
# Mas como estamos usando deps que lançam 401, o browser vai receber 401. 
# Para UX melhor, poderíamos ter um handler global.
