"""Carga de datos iniciales (catálogos) de LabControl Mecánica ESPOCH (FastAPI).

Inserta los 6 laboratorios de cómputo de la Facultad de Mecánica y un
usuario administrador inicial para poder probar el login.
Es idempotente: no duplica registros si ya existen.

Uso:
    python seed.py
"""
import os
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.models.laboratorio import Laboratorio
from app.models.usuario import Usuario

# Los 6 laboratorios de cómputo de la Facultad de Mecánica - ESPOCH.
LABORATORIOS = [
    {"nombre": "Laboratorio 1", "ubicacion": "Facultad de Mecánica - ESPOCH"},
    {"nombre": "Laboratorio 2", "ubicacion": "Facultad de Mecánica - ESPOCH"},
    {"nombre": "Laboratorio 3", "ubicacion": "Facultad de Mecánica - ESPOCH"},
    {"nombre": "Laboratorio 4", "ubicacion": "Facultad de Mecánica - ESPOCH"},
    {"nombre": "Laboratorio 5", "ubicacion": "Facultad de Mecánica - ESPOCH"},
    {"nombre": "Laboratorio 6", "ubicacion": "Facultad de Mecánica - ESPOCH"},
]


def seed_laboratorios(db: Session) -> int:
    creados = 0
    for data in LABORATORIOS:
        existe = db.query(Laboratorio).filter(Laboratorio.nombre == data["nombre"]).first()
        if not existe:
            db.add(Laboratorio(**data))
            creados += 1
    return creados


def seed_admin(db: Session) -> bool:
    """Crea un administrador inicial si no existe ninguno."""
    if db.query(Usuario).filter(Usuario.usuario == "admin").first():
        return False
    admin = Usuario(usuario="admin", perfil="administrador", activo=True)
    admin.set_password(os.environ.get("ADMIN_PASSWORD", "admin123"))
    db.add(admin)
    return True


def run_seed() -> None:
    # Asegura que las tablas existan en SQLite
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        n_labs = seed_laboratorios(db)
        admin_creado = seed_admin(db)
        db.commit()
        print(f"Laboratorios insertados: {n_labs} (de {len(LABORATORIOS)})")
        if admin_creado:
            print("Usuario 'admin' creado (perfil administrador).")
            print("  >> Contraseña por defecto 'admin123' — cámbiala cuanto antes.")
        else:
            print("Usuario 'admin' ya existía: sin cambios.")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
