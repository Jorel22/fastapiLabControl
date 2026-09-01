"""Modelo Usuario (RF-001 / RF-005 / NFR-003).

Representa a los usuarios del sistema con perfil 'administrador'
(técnico, escritura) o 'consulta' (decano, DTIC, solo lectura).
"""
from sqlalchemy import Boolean, CheckConstraint, Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.security import hash_password, verify_password

PERFILES = ("administrador", "consulta")


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(
            "perfil IN ('administrador', 'consulta')", name="ck_usuario_perfil"
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    perfil = Column(String(20), nullable=False, default="consulta")
    activo = Column(Boolean, nullable=False, default=True)

    mantenimientos = relationship("Mantenimiento", back_populates="usuario")
    auditorias = relationship("Auditoria", back_populates="usuario")

    def set_password(self, password: str) -> None:
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        return verify_password(password, self.password_hash)

    @property
    def es_administrador(self) -> bool:
        return self.perfil == "administrador"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "usuario": self.usuario,
            "perfil": self.perfil,
            "activo": self.activo,
        }

    def __repr__(self) -> str:
        return f"<Usuario {self.usuario} ({self.perfil})>"
