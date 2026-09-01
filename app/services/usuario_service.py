"""Servicio de gestión de cuentas (RF-005).

El administrador gestiona las cuentas de consulta (decano, DTIC):
creación, desactivación/activación y restablecimiento de credenciales.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.usuario import Usuario, PERFILES
from app.services.auditoria import registrar_auditoria


class UsuarioDuplicadoError(ValueError):
    """Ya existe un usuario con ese nombre."""


class PerfilInvalidoError(ValueError):
    """El perfil debe ser 'administrador' o 'consulta'."""


class UsuarioNoEncontradoError(LookupError):
    """No existe el usuario solicitado."""


def listar_usuarios(db: Optional[Session] = None):
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        return db.query(Usuario).order_by(Usuario.usuario.asc()).all()
    finally:
        if session_created:
            db.close()


def obtener_usuario(usuario_id: int, db: Optional[Session] = None) -> Usuario:
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        u = db.get(Usuario, usuario_id)
        if u is None:
            raise UsuarioNoEncontradoError(usuario_id)
        return u
    finally:
        if session_created:
            db.close()


def crear_cuenta(
    usuario: str, password: str, perfil: str = "consulta", usuario_creador_id: Optional[int] = None, db: Optional[Session] = None
) -> Usuario:
    """Crea una cuenta (por defecto, de consulta) (RF-005 · CA-005.1)."""
    usuario = (usuario or "").strip()
    if perfil not in PERFILES:
        raise PerfilInvalidoError("Perfil inválido.")

    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        if db.query(Usuario).filter(Usuario.usuario == usuario).first():
            raise UsuarioDuplicadoError(f"Ya existe el usuario '{usuario}'.")

        u = Usuario(usuario=usuario, perfil=perfil, activo=True)
        u.set_password(password)
        db.add(u)
        registrar_auditoria("usuarios", "alta", usuario, detalle={"perfil": perfil}, usuario_id=usuario_creador_id, db=db)
        db.commit()
        db.refresh(u)
        return u
    finally:
        if session_created:
            db.close()


def cambiar_estado(usuario_id: int, activo: bool, usuario_editor_id: Optional[int] = None, db: Optional[Session] = None) -> Usuario:
    """Activa o desactiva una cuenta (RF-005)."""
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        u = obtener_usuario(usuario_id, db=db)
        u.activo = activo
        operacion = "reactivacion" if activo else "baja"
        registrar_auditoria("usuarios", operacion, str(usuario_id), usuario_id=usuario_editor_id, db=db)
        db.commit()
        db.refresh(u)
        return u
    finally:
        if session_created:
            db.close()


def restablecer_password(usuario_id: int, nueva_password: str, usuario_editor_id: Optional[int] = None, db: Optional[Session] = None) -> Usuario:
    """Restablece la contraseña de una cuenta (RF-005 · CA-005.1)."""
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        u = obtener_usuario(usuario_id, db=db)
        u.set_password(nueva_password)
        registrar_auditoria("usuarios", "edicion", str(usuario_id), detalle={"reset": True}, usuario_id=usuario_editor_id, db=db)
        db.commit()
        db.refresh(u)
        return u
    finally:
        if session_created:
            db.close()
