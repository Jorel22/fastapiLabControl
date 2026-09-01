"""Modelo Mantenimiento (RF-003 / RF-006).

Intervención preventiva o correctiva sobre un bien. La validación de
'fecha no posterior a la actual' (CA-003.3) y 'tipo obligatorio'
(CA-003.2) se aplica en la capa de servicio.
"""
from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

TIPOS = ("preventivo", "correctivo")


class Mantenimiento(Base):
    __tablename__ = "mantenimientos"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('preventivo', 'correctivo')", name="ck_mantenimiento_tipo"
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_bien = Column(
        String(50), ForeignKey("bienes.codigo_bien"), nullable=False, index=True
    )
    tipo = Column(String(20), nullable=False)
    fecha = Column(Date, nullable=False)
    observaciones = Column(Text)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))

    bien = relationship("Bien", back_populates="mantenimientos")
    usuario = relationship("Usuario", back_populates="mantenimientos")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "codigo_bien": self.codigo_bien,
            "tipo": self.tipo,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "observaciones": self.observaciones,
            "usuario_id": self.usuario_id,
            "usuario": self.usuario.usuario if self.usuario else None,
        }

    def __repr__(self) -> str:
        return f"<Mantenimiento {self.tipo} {self.fecha} bien={self.codigo_bien}>"
