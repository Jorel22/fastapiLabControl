"""Modelo Laboratorio.

Un laboratorio alberga muchos bienes (ER §5.2 del SRS). Son los 6
laboratorios de cómputo de la Facultad de Mecánica de la ESPOCH.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Laboratorio(Base):
    __tablename__ = "laboratorios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    ubicacion = Column(String(150))

    bienes = relationship("Bien", back_populates="laboratorio")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "ubicacion": self.ubicacion,
        }

    def __repr__(self) -> str:
        return f"<Laboratorio {self.nombre}>"
