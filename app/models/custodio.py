"""Modelo Custodio.

Persona responsable de uno o varios bienes (ER §5.2 del SRS),
requerido por las Normas de Control Interno 406-05 (RD-001).
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Custodio(Base):
    __tablename__ = "custodios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(120), nullable=False)
    cargo = Column(String(80))

    bienes = relationship("Bien", back_populates="custodio")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "cargo": self.cargo,
        }

    def __repr__(self) -> str:
        return f"<Custodio {self.nombre}>"
