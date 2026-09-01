"""Modelo Auditoria (NFR-003 / RD-003).

Registra cada operación de escritura (alta, edición, baja,
reactivación) para mantener la traza requerida por las Normas de
Control Interno (serie 410).
"""
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

OPERACIONES = ("alta", "edicion", "baja", "reactivacion")


def utcnow():
    return datetime.now(timezone.utc)


class Auditoria(Base):
    __tablename__ = "auditoria"
    __table_args__ = (
        CheckConstraint(
            "operacion IN ('alta', 'edicion', 'baja', 'reactivacion')",
            name="ck_auditoria_operacion",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    entidad = Column(String(50), nullable=False)
    operacion = Column(String(20), nullable=False)
    registro_id = Column(String(50), nullable=False)
    fecha = Column(DateTime, nullable=False, default=utcnow)
    detalle = Column(Text)  # JSON serializado con el cambio.

    usuario = relationship("Usuario", back_populates="auditorias")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "usuario": self.usuario.usuario if self.usuario else None,
            "entidad": self.entidad,
            "operacion": self.operacion,
            "registro_id": self.registro_id,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "detalle": self.detalle,
        }

    def __repr__(self) -> str:
        return f"<Auditoria {self.operacion} {self.entidad}#{self.registro_id}>"
