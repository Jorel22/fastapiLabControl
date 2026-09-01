"""Esquemas Pydantic para autenticación."""
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    usuario: Optional[str] = Field(None, description="Nombre de usuario", examples=["tecnico"])
    password: Optional[str] = Field(None, description="Contraseña", examples=["admin123"])


class UsuarioResponse(BaseModel):
    id: int
    usuario: str
    perfil: str
    activo: bool


class LoginResponse(BaseModel):
    mensaje: str
    usuario: UsuarioResponse


class PerfilResponse(BaseModel):
    usuario: UsuarioResponse


class MessageResponse(BaseModel):
    mensaje: str
