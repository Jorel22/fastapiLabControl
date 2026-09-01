"""Router de autenticación por JWT con cookies HttpOnly y soporte Bearer Token."""
from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
)
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, LoginResponse, PerfilResponse

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

# Mensaje único para cualquier fallo de autenticación.
ERROR_GENERICO = "Usuario o contraseña incorrectos."


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Inicio de sesión. Genera el token JWT y lo adjunta en una cookie HttpOnly."""
    usuario_str = (data.usuario or "").strip() if data.usuario else ""
    password_str = (data.password or "").strip() if data.password else ""

    if not usuario_str or not password_str:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": ERROR_GENERICO},
        )

    usuario = db.query(Usuario).filter(Usuario.usuario == usuario_str).first()

    # Validación combinada: existencia + contraseña + cuenta activa.
    if usuario is None or not usuario.check_password(password_str) or not usuario.activo:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": ERROR_GENERICO},
        )

    access_token = create_access_token(identity=str(usuario.id))

    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "mensaje": f"Bienvenido, {usuario.usuario}.",
            "usuario": usuario.to_dict(),
        },
    )

    response.set_cookie(
        key=settings.JWT_ACCESS_COOKIE_NAME,
        value=access_token,
        httponly=True,
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRES_MINUTES * 60,
        samesite="lax",
        path="/",
    )
    return response


@router.post("/logout")
def logout():
    """Cierre de sesión. Invalida la cookie HttpOnly."""
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"mensaje": "Sesión cerrada."},
    )
    response.delete_cookie(
        key=settings.JWT_ACCESS_COOKIE_NAME,
        path="/",
    )
    return response


@router.get("/perfil")
def perfil(current_user: Usuario = Depends(get_current_user)):
    """Muestra los datos del usuario autenticado."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"usuario": current_user.to_dict()},
    )
