"""Esquemas Pydantic para gestión de usuarios."""
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.auth import UsuarioResponse


class UsuarioCreate(BaseModel):
    usuario: Optional[str] = Field(None, description="Nombre del usuario", examples=["decano"])
    password: Optional[str] = Field(None, description="Contraseña", examples=["clave123"])
    perfil: Optional[str] = Field("consulta", description="Perfil de usuario (administrador o consulta)", examples=["consulta"])


class UsuarioResetPassword(BaseModel):
    password: Optional[str] = Field(None, description="Nueva contraseña (mínimo 6 caracteres)", examples=["nueva123"])


class UsuariosListResponse(BaseModel):
    usuarios: List[UsuarioResponse]
