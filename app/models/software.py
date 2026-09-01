"""Modelo Software (RF-007).

Software y licencias instalados en una computadora (SO, programas de
ingeniería, antivirus Kaspersky con nº de escaneos). El estado de la
licencia permite señalar las próximas a vencer (CA-007.2).
"""
import datetime
from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base

LICENCIAS = ("activa", "vencida")

DIAS_ALERTA_VENCIMIENTO = 30


class Software(Base):
    __tablename__ = "software"
    __table_args__ = (
        CheckConstraint(
            "licencia IN ('activa', 'vencida')", name="ck_software_licencia"
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_bien = Column(
        String(50), ForeignKey("bienes.codigo_bien"), nullable=False, index=True
    )
    nombre = Column(String(150), nullable=False)
    licencia = Column(String(20), default="activa")
    fecha_instalacion = Column(Date)
    vencimiento = Column(Date)
    num_escaneos = Column(Integer, default=0)

    bien = relationship("Bien", back_populates="software")

    @property
    def dias_para_vencer(self):
        """Días restantes hasta el vencimiento (negativo si ya venció)."""
        if not self.vencimiento:
            return None
        return (self.vencimiento - datetime.date.today()).days

    @property
    def estado_licencia(self) -> str:
        """Estado calculado: 'vencida' | 'por_vencer' | 'vigente' (CA-007.2)."""
        dias = self.dias_para_vencer
        if dias is None:
            return self.licencia or "vigente"
        if dias < 0:
            return "vencida"
        if dias <= DIAS_ALERTA_VENCIMIENTO:
            return "por_vencer"
        return "vigente"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "codigo_bien": self.codigo_bien,
            "nombre": self.nombre,
            "licencia": self.licencia,
            "fecha_instalacion": self.fecha_instalacion.isoformat() if self.fecha_instalacion else None,
            "vencimiento": self.vencimiento.isoformat() if self.vencimiento else None,
            "num_escaneos": self.num_escaneos,
            "estado_licencia": self.estado_licencia,
            "dias_para_vencer": self.dias_para_vencer,
        }

    def __repr__(self) -> str:
        return f"<Software {self.nombre} ({self.licencia}) bien={self.codigo_bien}>"
