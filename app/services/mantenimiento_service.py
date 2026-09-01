"""Servicio de mantenimientos e histórico técnico (RF-003 · RF-006).

Reglas de negocio:
- El tipo es obligatorio y debe ser 'preventivo' o 'correctivo' (CA-003.2).
- La fecha no puede ser posterior a la actual (CA-003.3).
- El histórico se devuelve en orden cronológico (CA-006.1 · NFR-001).
"""
import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.mantenimiento import Mantenimiento, TIPOS
from app.services.auditoria import registrar_auditoria
from app.services.bien_service import obtener_bien


class TipoInvalidoError(ValueError):
    """El tipo de mantenimiento es obligatorio y acotado (CA-003.2)."""


class FechaFuturaError(ValueError):
    """La fecha del mantenimiento no puede ser posterior a hoy (CA-003.3)."""


def registrar_mantenimiento(
    codigo_bien: str,
    tipo: str,
    fecha: datetime.date,
    observaciones: Optional[str] = None,
    usuario_id: Optional[int] = None,
    db: Optional[Session] = None,
) -> Mantenimiento:
    """Registra un mantenimiento sobre un bien existente (RF-003).

    Raises:
        BienNoEncontradoError: si el bien no existe.
        TipoInvalidoError: si falta el tipo o no es válido (CA-003.2).
        FechaFuturaError: si la fecha es futura (CA-003.3).
    """
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        obtener_bien(codigo_bien, db=db)  # lanza BienNoEncontradoError si no existe

        if tipo not in TIPOS:
            raise TipoInvalidoError("Selecciona un tipo de mantenimiento válido.")

        if isinstance(fecha, str):
            fecha = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()

        if fecha is None or fecha > datetime.date.today():
            raise FechaFuturaError("La fecha no puede ser posterior a la actual.")

        mant = Mantenimiento(
            codigo_bien=codigo_bien,
            tipo=tipo,
            fecha=fecha,
            observaciones=(observaciones or "").strip() or None,
            usuario_id=usuario_id,
        )
        db.add(mant)
        registrar_auditoria(
            "mantenimientos", "alta", codigo_bien, detalle={"tipo": tipo, "fecha": str(fecha)}, usuario_id=usuario_id, db=db
        )
        db.commit()
        db.refresh(mant)
        return mant
    finally:
        if session_created:
            db.close()


def obtener_historico(codigo_bien: str, db: Optional[Session] = None):
    """Devuelve (bien, mantenimientos) en orden cronológico (RF-006).

    El bien se obtiene con obtener_bien, que lanza BienNoEncontradoError
    si el código no existe (CA-006.2). Un bien sin mantenimientos devuelve
    una lista vacía (CA-006.3).
    """
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        bien = obtener_bien(codigo_bien, db=db)
        historico = (
            db.query(Mantenimiento)
            .filter(Mantenimiento.codigo_bien == codigo_bien)
            .order_by(Mantenimiento.fecha.asc(), Mantenimiento.id.asc())
            .all()
        )
        return bien, historico
    finally:
        if session_created:
            db.close()
