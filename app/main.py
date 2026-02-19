# SISCONT - Deploy V42 (NF File Upload & Modal Fix) - 19/02/2026 19:55
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import traceback
from app.routers import auth, diretorias, usuarios, vendas, dashboard, clientes, linhas_produto

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="SisCont", version="1.0.1", lifespan=lifespan)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

@app.get("/heal-v42")
async def heal_v42():
    from sqlalchemy import text
    from app.database import engine
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print("V42 HEALING: Adding documento_pdf to notas_fiscais...")
            try:
                conn.execute(text("ALTER TABLE notas_fiscais ADD COLUMN IF NOT EXISTS documento_pdf VARCHAR(255)"))
                print("V42 HEALING: Column added successfully.")
            except Exception as ex:
                 print(f"V42 HEALING: Column might already exist or error: {ex}")
            return {"status": "V42 Ecosystem Healed"}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401: return RedirectResponse(url="/login")
    if exc.status_code == 403: return RedirectResponse(url="/dashboard")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"CRITICAL ERROR: {traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor", "error": str(exc)})

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def root():
    return RedirectResponse(url="/login")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(diretorias.router)
app.include_router(usuarios.router)
app.include_router(vendas.router)
app.include_router(clientes.router)
app.include_router(linhas_produto.router)
