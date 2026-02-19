"""Schemas Pydantic para Autenticação e Usuários."""
from pydantic import BaseModel, EmailStr
from app.models.usuario import PerfilEnum


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    perfil: PerfilEnum = PerfilEnum.usuario
    diretoria_id: int | None = None
    ativo: bool = True


class UsuarioCreate(UsuarioBase):
    senha: str


class UsuarioResponse(UsuarioBase):
    id: int

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str
