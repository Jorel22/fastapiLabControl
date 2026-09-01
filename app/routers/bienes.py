"""Router de inventario de bienes (API REST)."""
import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.bien import ESTADOS, TIPOS_EQUIPO
from app.models.custodio import Custodio
from app.models.laboratorio import Laboratorio
from app.models.usuario import Usuario
from app.schemas.bien import BienCreate, BienUpdate
from app.schemas.software import SoftwareCreate
from app.services import bien_service, software_service

router = APIRouter(prefix="/api/bienes", tags=["Bienes"])


@router.get("")
def listar(
    laboratorio_id: Optional[int] = None,
    tipo: Optional[str] = None,
    estado: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista el inventario con filtros opcionales."""
    bienes = bien_service.listar_bienes(laboratorio_id, tipo, estado, db=db)

    labs = db.query(Laboratorio).order_by(Laboratorio.nombre).all()
    custodios = db.query(Custodio).order_by(Custodio.nombre).all()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "bienes": [b.to_dict() for b in bienes],
            "catalogos": {
                "laboratorios": [l.to_dict() for l in labs],
                "custodios": [c.to_dict() for c in custodios],
                "tipos": list(TIPOS_EQUIPO),
                "estados": list(ESTADOS),
            },
        },
    )


@router.get("/{codigo}")
def obtener(
    codigo: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtiene un bien específico por código."""
    try:
        bien = bien_service.obtener_bien(codigo, db=db)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"bien": bien.to_dict()})
    except bien_service.BienNoEncontradoError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"No existe el bien '{codigo}'"},
        )


@router.post("")
def nuevo(
    data: BienCreate,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Registra un nuevo bien."""
    try:
        bien = bien_service.crear_bien(
            data.model_dump(),
            usuario_id=current_user.id,
            db=db,
        )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "mensaje": f"Bien '{bien.codigo_bien}' registrado.",
                "bien": bien.to_dict(),
            },
        )
    except bien_service.CodigoDuplicadoError as exc:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"error": str(exc)})
    except bien_service.CodigoRequeridoError as exc:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"error": str(exc)})


@router.put("/{codigo}")
def editar(
    codigo: str,
    data: BienUpdate,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Edita un bien conservando histórico y auditoría."""
    try:
        bien = bien_service.actualizar_bien(
            codigo,
            data.model_dump(exclude_unset=False),
            usuario_id=current_user.id,
            db=db,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "mensaje": f"Bien '{codigo}' actualizado.",
                "bien": bien.to_dict(),
            },
        )
    except bien_service.BienNoEncontradoError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"No existe el bien '{codigo}'"},
        )


@router.post("/{codigo}/baja")
def baja(
    codigo: str,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Da de baja un bien (baja lógica)."""
    try:
        bien_service.dar_de_baja(codigo, usuario_id=current_user.id, db=db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"mensaje": f"Bien '{codigo}' dado de baja."},
        )
    except bien_service.BienNoEncontradoError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"No existe el bien '{codigo}'"},
        )


@router.post("/{codigo}/reactivar")
def reactivar(
    codigo: str,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reactiva un bien dado de baja."""
    try:
        bien_service.reactivar(codigo, usuario_id=current_user.id, db=db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"mensaje": f"Bien '{codigo}' reactivado."},
        )
    except bien_service.BienNoEncontradoError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"No existe el bien '{codigo}'"},
        )


@router.get("/{codigo}/software")
def listar_software(
    codigo: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista software/licencias de un equipo."""
    try:
        bien = bien_service.obtener_bien(codigo, db=db)
        softwares = software_service.listar_software(codigo, db=db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "bien": bien.to_dict(),
                "softwares": [s.to_dict() for s in softwares],
            },
        )
    except bien_service.BienNoEncontradoError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"No existe el bien '{codigo}'"},
        )


@router.post("/{codigo}/software")
def agregar_software(
    codigo: str,
    data: SoftwareCreate,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Registra software/licencias en un equipo."""
    fecha_instalacion = None
    vencimiento = None
    if data.fecha_instalacion:
        try:
            fecha_instalacion = datetime.datetime.strptime(data.fecha_instalacion, "%Y-%m-%d").date()
        except ValueError:
            pass
    if data.vencimiento:
        try:
            vencimiento = datetime.datetime.strptime(data.vencimiento, "%Y-%m-%d").date()
        except ValueError:
            pass

    try:
        s = software_service.agregar_software(
            codigo_bien=codigo,
            nombre=data.nombre or "",
            licencia=data.licencia or "activa",
            fecha_instalacion=fecha_instalacion,
            vencimiento=vencimiento,
            num_escaneos=data.num_escaneos or 0,
            usuario_id=current_user.id,
            db=db,
        )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "mensaje": "Software registrado.",
                "software": s.to_dict(),
            },
        )
    except bien_service.BienNoEncontradoError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"No existe el bien '{codigo}'"},
        )
    except software_service.NombreSoftwareRequeridoError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": str(exc)},
        )
