"""Servicio de inventario de bienes (RF-002 · RF-008 · RF-011).

Concentra las reglas de negocio y la auditoría de las operaciones
sobre bienes, separadas de la capa de rutas.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.bien import Bien
from app.services.auditoria import registrar_auditoria


class CodigoRequeridoError(ValueError):
    """El código del bien es obligatorio (CA-002.2)."""


class CodigoDuplicadoError(ValueError):
    """Ya existe un bien con ese código del bien (CA-002.3)."""


class BienNoEncontradoError(LookupError):
    """No existe el bien solicitado."""


def listar_bienes(
    laboratorio_id: Optional[int] = None,
    tipo: Optional[str] = None,
    estado: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Lista bienes aplicando filtros opcionales (RF-011 · CA-011.1)."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        query = db.query(Bien)
        if laboratorio_id:
            query = query.filter(Bien.laboratorio_id == laboratorio_id)
        if tipo:
            query = query.filter(Bien.tipo == tipo)
        if estado:
            query = query.filter(Bien.estado == estado)
        return query.order_by(Bien.codigo_bien).all()
    finally:
        if close_db:
            db.close()


def obtener_bien(codigo_bien: str, db: Optional[Session] = None) -> Bien:
    """Obtiene un bien por código. Lanza BienNoEncontradoError si no existe."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        bien = db.get(Bien, codigo_bien)
        if bien is None:
            raise BienNoEncontradoError(codigo_bien)
        return bien
    finally:
        if close_db:
            db.close()


def crear_bien(data: dict, usuario_id: Optional[int] = None, db: Optional[Session] = None) -> Bien:
    """Registra un bien validando código obligatorio y único (RF-002).

    Raises:
        CodigoRequeridoError: si falta el código del bien (CA-002.2).
        CodigoDuplicadoError: si el código ya existe (CA-002.3).
    """
    codigo = (data.get("codigo_bien") or "").strip()
    if not codigo:
        raise CodigoRequeridoError("El código del bien es obligatorio.")

    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        if db.get(Bien, codigo) is not None:
            raise CodigoDuplicadoError(f"Ya existe un bien con el código '{codigo}'.")

        # Convertir empty strings o 0 en IDs a None
        lab_id = data.get("laboratorio_id")
        if lab_id == 0 or lab_id == "" or lab_id == "0":
            lab_id = None
        elif lab_id is not None:
            lab_id = int(lab_id)

        cust_id = data.get("custodio_id")
        if cust_id == 0 or cust_id == "" or cust_id == "0":
            cust_id = None
        elif cust_id is not None:
            cust_id = int(cust_id)

        tipo_val = data.get("tipo")
        if not tipo_val:
            tipo_val = None

        bien = Bien(
            codigo_bien=codigo,
            numero_serie=(data.get("numero_serie") or "").strip() or None,
            nombre=(data.get("nombre") or "").strip(),
            descripcion=(data.get("descripcion") or "").strip() or None,
            tipo=tipo_val,
            laboratorio_id=lab_id,
            custodio_id=cust_id,
            estado="activo",
        )
        db.add(bien)
        registrar_auditoria("bienes", "alta", codigo, detalle={"nombre": bien.nombre}, usuario_id=usuario_id, db=db)
        db.commit()
        db.refresh(bien)
        return bien
    finally:
        if session_created:
            db.close()


def actualizar_bien(codigo_bien: str, data: dict, usuario_id: Optional[int] = None, db: Optional[Session] = None) -> Bien:
    """Edita un bien conservando su histórico y dejando auditoría (RF-004 · CA-004.1)."""
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        bien = db.get(Bien, codigo_bien)
        if bien is None:
            raise BienNoEncontradoError(codigo_bien)

        cambios = {}
        for campo in ("nombre", "numero_serie", "descripcion", "tipo", "laboratorio_id", "custodio_id"):
            if campo in data:
                valor = data[campo]
                if campo in ("laboratorio_id", "custodio_id"):
                    if valor == 0 or valor == "" or valor == "0":
                        valor = None
                    elif valor is not None:
                        valor = int(valor)
                elif isinstance(valor, str):
                    valor = valor.strip() or None

                if getattr(bien, campo) != valor:
                    cambios[campo] = valor
                    setattr(bien, campo, valor)

        if cambios:
            registrar_auditoria("bienes", "edicion", codigo_bien, detalle=cambios, usuario_id=usuario_id, db=db)
            db.commit()
            db.refresh(bien)
        return bien
    finally:
        if session_created:
            db.close()


def dar_de_baja(codigo_bien: str, usuario_id: Optional[int] = None, db: Optional[Session] = None) -> Bien:
    """Baja lógica conservando el histórico (RF-008 · CA-008.1)."""
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        bien = db.get(Bien, codigo_bien)
        if bien is None:
            raise BienNoEncontradoError(codigo_bien)

        bien.estado = "dado_de_baja"
        registrar_auditoria("bienes", "baja", codigo_bien, usuario_id=usuario_id, db=db)
        db.commit()
        db.refresh(bien)
        return bien
    finally:
        if session_created:
            db.close()


def reactivar(codigo_bien: str, usuario_id: Optional[int] = None, db: Optional[Session] = None) -> Bien:
    """Reactiva un bien dado de baja por error (RF-008 · CA-008.2)."""
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        bien = db.get(Bien, codigo_bien)
        if bien is None:
            raise BienNoEncontradoError(codigo_bien)

        bien.estado = "activo"
        registrar_auditoria("bienes", "reactivacion", codigo_bien, usuario_id=usuario_id, db=db)
        db.commit()
        db.refresh(bien)
        return bien
    finally:
        if session_created:
            db.close()
