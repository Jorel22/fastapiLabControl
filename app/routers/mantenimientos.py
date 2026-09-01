"""Router de mantenimientos e histórico técnico (API REST)."""
import datetime
from typing import Optional
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.usuario import Usuario
from app.schemas.mantenimiento import MantenimientoCreate
from app.services import bien_service, mantenimiento_service

router = APIRouter(prefix="/api/bienes", tags=["Mantenimientos"])


@router.post("/{codigo}/mantenimientos")
def registrar(
    codigo: str,
    data: MantenimientoCreate,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Registra un mantenimiento sobre un bien."""
    tipo = data.tipo
    fecha_str = data.fecha
    observaciones = data.observaciones

    if not tipo or not fecha_str:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "El tipo y la fecha son obligatorios."},
        )

    try:
        fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Formato de fecha inválido. Utilice AAAA-MM-DD."},
        )

    try:
        mantenimiento_service.registrar_mantenimiento(
            codigo_bien=codigo,
            tipo=tipo,
            fecha=fecha,
            observaciones=observaciones,
            usuario_id=current_user.id,
            db=db,
        )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"mensaje": "Mantenimiento registrado y agregado al histórico."},
        )
    except bien_service.BienNoEncontradoError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"No existe el bien '{codigo}'."},
        )
    except mantenimiento_service.TipoInvalidoError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": str(exc)},
        )
    except mantenimiento_service.FechaFuturaError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": str(exc)},
        )


@router.get("/{codigo}/historico")
def historico(
    codigo: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Muestra el histórico cronológico de un equipo."""
    try:
        bien, registros = mantenimiento_service.obtener_historico(codigo, db=db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "bien": bien.to_dict(),
                "registros": [r.to_dict() for r in registros],
            },
        )
    except bien_service.BienNoEncontradoError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"No se encontró ningún equipo con el código '{codigo}'."},
        )
