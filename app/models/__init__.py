"""Registro central de modelos SQLAlchemy."""
from app.models.auditoria import Auditoria
from app.models.bien import Bien
from app.models.custodio import Custodio
from app.models.laboratorio import Laboratorio
from app.models.mantenimiento import Mantenimiento
from app.models.software import Software
from app.models.usuario import Usuario

__all__ = [
    "Usuario",
    "Laboratorio",
    "Custodio",
    "Bien",
    "Mantenimiento",
    "Software",
    "Auditoria",
]
