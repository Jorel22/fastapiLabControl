"""Servicio de software y licencias (RF-007)."""
import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.software import Software
from app.services.auditoria import registrar_auditoria
from app.services.bien_service import obtener_bien


class NombreSoftwareRequeridoError(ValueError):
    """El nombre del software es obligatorio."""


def listar_software(codigo_bien: str, db: Optional[Session] = None):
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        obtener_bien(codigo_bien, db=db)  # valida existencia del equipo
        return (
            db.query(Software)
            .filter(Software.codigo_bien == codigo_bien)
            .order_by(Software.nombre.asc())
            .all()
        )
    finally:
        if session_created:
            db.close()


def agregar_software(
    codigo_bien: str,
    nombre: str,
    licencia: str = "activa",
    fecha_instalacion: Optional[datetime.date] = None,
    vencimiento: Optional[datetime.date] = None,
    num_escaneos: int = 0,
    usuario_id: Optional[int] = None,
    db: Optional[Session] = None,
) -> Software:
    """Registra software/licencia en un equipo (RF-007 · CA-007.1)."""
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        obtener_bien(codigo_bien, db=db)
        if not (nombre or "").strip():
            raise NombreSoftwareRequeridoError("El nombre del software es obligatorio.")

        if isinstance(fecha_instalacion, str):
            fecha_instalacion = datetime.datetime.strptime(fecha_instalacion, "%Y-%m-%d").date()
        if isinstance(vencimiento, str):
            vencimiento = datetime.datetime.strptime(vencimiento, "%Y-%m-%d").date()

        sw = Software(
            codigo_bien=codigo_bien,
            nombre=nombre.strip(),
            licencia=licencia or "activa",
            fecha_instalacion=fecha_instalacion,
            vencimiento=vencimiento,
            num_escaneos=num_escaneos or 0,
        )
        db.add(sw)
        registrar_auditoria("software", "alta", codigo_bien, detalle={"nombre": sw.nombre}, usuario_id=usuario_id, db=db)
        db.commit()
        db.refresh(sw)
        return sw
    finally:
        if session_created:
            db.close()
