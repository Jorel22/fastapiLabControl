"""Router de gestión de cuentas de usuario (API REST)."""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResetPassword
from app.services import usuario_service

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])


@router.get("")
def index(
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lista las cuentas de usuario."""
    usuarios = usuario_service.listar_usuarios(db=db)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"usuarios": [u.to_dict() for u in usuarios]},
    )


@router.post("")
def crear(
    data: UsuarioCreate,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Crea una nueva cuenta de usuario."""
    usuario = data.usuario
    password = data.password
    perfil = data.perfil

    if not usuario or not password or not perfil:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Todos los campos son obligatorios."},
        )

    try:
        u = usuario_service.crear_cuenta(
            usuario=usuario,
            password=password,
            perfil=perfil,
            usuario_creador_id=current_user.id,
            db=db,
        )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "mensaje": f"Cuenta '{u.usuario}' creada con éxito.",
                "usuario": u.to_dict(),
            },
        )
    except usuario_service.UsuarioDuplicadoError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": str(exc)},
        )
    except usuario_service.PerfilInvalidoError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": str(exc)},
        )


@router.post("/{usuario_id}/estado")
def cambiar_estado(
    usuario_id: int,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Activa o desactiva una cuenta."""
    if usuario_id == current_user.id:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "No puedes desactivar tu propia cuenta."},
        )
    try:
        u = usuario_service.obtener_usuario(usuario_id, db=db)
        usuario_service.cambiar_estado(usuario_id, not u.activo, usuario_editor_id=current_user.id, db=db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "mensaje": f"Cuenta '{u.usuario}' actualizada.",
                "usuario": u.to_dict(),
            },
        )
    except usuario_service.UsuarioNoEncontradoError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "La cuenta no existe."},
        )


@router.post("/{usuario_id}/reset")
def reset(
    usuario_id: int,
    data: UsuarioResetPassword,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Restablece la contraseña de una cuenta."""
    password = data.password

    if not password or len(password) < 6:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "La nueva contraseña debe tener mínimo 6 caracteres."},
        )

    try:
        usuario_service.restablecer_password(usuario_id, password, usuario_editor_id=current_user.id, db=db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"mensaje": "Contraseña restablecida con éxito."},
        )
    except usuario_service.UsuarioNoEncontradoError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "La cuenta no existe."},
        )
