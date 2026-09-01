"""Modelo Bien (RF-002 / RF-008 / RF-011).

Equipo tecnológico institucional identificado por su código del bien
(PK natural que evita duplicados — CA-002.3). La baja es lógica vía el
campo 'estado', conservando el histórico (RF-008 / RD-001).
"""
from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

ESTADOS = ("activo", "dado_de_baja")

TIPOS_EQUIPO = (
    "computadora",
    "switch",
    "access_point",
    "proyector",
    "pantalla_interactiva",
    "aire_acondicionado",
    "otro",
)


class Bien(Base):
    __tablename__ = "bienes"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('activo', 'dado_de_baja')", name="ck_bien_estado"
        ),
    )

    codigo_bien = Column(String(50), primary_key=True)
    numero_serie = Column(String(100))
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text)
    tipo = Column(String(50), index=True)
    laboratorio_id = Column(Integer, ForeignKey("laboratorios.id"))
    custodio_id = Column(Integer, ForeignKey("custodios.id"))
    estado = Column(String(20), nullable=False, default="activo")

    laboratorio = relationship("Laboratorio", back_populates="bienes")
    custodio = relationship("Custodio", back_populates="bienes")
    mantenimientos = relationship(
        "Mantenimiento", back_populates="bien", cascade="all, delete-orphan"
    )
    software = relationship(
        "Software", back_populates="bien", cascade="all, delete-orphan"
    )

    @property
    def esta_activo(self) -> bool:
        return self.estado == "activo"

    def to_dict(self) -> dict:
        return {
            "codigo_bien": self.codigo_bien,
            "numero_serie": self.numero_serie,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "tipo": self.tipo,
            "laboratorio_id": self.laboratorio_id,
            "custodio_id": self.custodio_id,
            "estado": self.estado,
            "laboratorio": self.laboratorio.nombre if self.laboratorio else None,
            "custodio": self.custodio.nombre if self.custodio else None,
        }

    def __repr__(self) -> str:
        return f"<Bien {self.codigo_bien} - {self.nombre} ({self.estado})>"
