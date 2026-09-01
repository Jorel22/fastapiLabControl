"""Servicio de auditoría (NFR-003 · RD-003).

Registra cada operación de escritura (alta, edición, baja,
reactivación) en la tabla `auditoria`, dejando constancia del usuario
responsable. Las normas de control interno (serie 410) exigen esta
traza para auditorías y acreditación.
"""
import json
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.auditoria import Auditoria


def registrar_auditoria(
    entidad: str,
    operacion: str,
    registro_id: str,
    detalle: Optional[dict] = None,
    usuario_id: Optional[int] = None,
    commit: bool = False,
    db: Optional[Session] = None,
) -> Auditoria:
    """Añade una entrada de auditoría a la sesión.

    Args:
        entidad: nombre de la tabla afectada (p. ej. 'bienes').
        operacion: 'alta' | 'edicion' | 'baja' | 'reactivacion'.
        registro_id: identificador del registro afectado.
        detalle: datos del cambio (se serializan a JSON).
        usuario_id: id del responsable.
        commit: si True, confirma la transacción.
        db: sesión de SQLAlchemy. Si es None, se crea una sesión temporal.

    Returns:
        La instancia de Auditoria creada.
    """
    close_on_finish = False
    if db is None:
        db = SessionLocal()
        close_on_finish = not commit  # si no hay commit, cerramos al salir

    entrada = Auditoria(
        usuario_id=usuario_id,
        entidad=entidad,
        operacion=operacion,
        registro_id=str(registro_id),
        detalle=json.dumps(detalle, ensure_ascii=False) if detalle else None,
    )
    db.add(entrada)
    if commit:
        db.commit()
    
    if close_on_finish:
        db.close()

    return entrada
