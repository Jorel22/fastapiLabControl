"""Datos de demostración de LabControl Mecánica ESPOCH (FastAPI).

Carga un conjunto realista de bienes, mantenimientos y software en los
6 laboratorios para la presentación del MVP. Es idempotente y se apoya
en el seed base (`seed.py`) para los laboratorios y el usuario admin.

Uso:
    python seed.py        # 6 laboratorios + usuario admin
    python seed_demo.py   # datos de demostración
"""
import datetime
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.models.bien import Bien
from app.models.custodio import Custodio
from app.models.laboratorio import Laboratorio
from app.models.usuario import Usuario
from app.services import (
    bien_service,
    mantenimiento_service,
    software_service,
    usuario_service,
)

HOY = datetime.date.today()


def _dias(n: int) -> datetime.date:
    """Fecha en el pasado: hoy menos n días (para instalaciones/mantenimientos)."""
    return HOY - datetime.timedelta(days=n)


def _futuro(n: int) -> datetime.date:
    """Fecha relativa a hoy: positivo = futuro, negativo = pasado (vencimientos)."""
    return HOY + datetime.timedelta(days=n)


CUSTODIOS = [
    {"nombre": "Ing. Carlos Pérez", "cargo": "Técnico de Laboratorios"},
    {"nombre": "Ing. María Yánez", "cargo": "Asistente técnica"},
]

# (codigo_bien, nombre, tipo, lab_index, custodio_index)
BIENES = [
    ("ESPOCH-PC-001", "PC Dell OptiPlex 7090", "computadora", 0, 0),
    ("ESPOCH-PC-002", "PC HP ProDesk 400", "computadora", 0, 0),
    ("ESPOCH-PC-003", "PC Lenovo ThinkCentre", "computadora", 1, 1),
    ("ESPOCH-SW-001", "Switch Cisco Catalyst 2960", "switch", 1, 0),
    ("ESPOCH-AP-001", "Access Point Ubiquiti UAP", "access_point", 2, 1),
    ("ESPOCH-PROY-001", "Proyector Epson PowerLite", "proyector", 3, 0),
    ("ESPOCH-PI-001", "Pantalla interactiva ViewSonic", "pantalla_interactiva", 4, 1),
    ("ESPOCH-AC-001", "Aire acondicionado LG 24000 BTU", "aire_acondicionado", 5, 0),
]

# (codigo_bien, tipo, dias_atras, observaciones)
MANTENIMIENTOS = [
    ("ESPOCH-PC-001", "preventivo", 120, "Limpieza interna y desempolvado."),
    ("ESPOCH-PC-001", "correctivo", 30, "Reemplazo de HDD por SSD de 480 GB."),
    ("ESPOCH-PC-002", "preventivo", 90, "Actualización de controladores."),
    ("ESPOCH-PC-003", "correctivo", 15, "Cambio de memoria RAM defectuosa."),
    ("ESPOCH-SW-001", "preventivo", 60, "Revisión de puertos y firmware."),
    ("ESPOCH-PROY-001", "correctivo", 45, "Cambio de lámpara del proyector."),
    ("ESPOCH-AC-001", "preventivo", 10, "Limpieza de filtros y carga de gas."),
]

# (codigo_bien, nombre, licencia, dias_instalacion_atras, dias_hasta_vencimiento, escaneos)
# dias_hasta_vencimiento: positivo = futuro · negativo = ya vencida · None = sin vencimiento
SOFTWARE = [
    ("ESPOCH-PC-001", "Windows 11 Pro", "activa", 200, None, 0),     # sin vencimiento
    ("ESPOCH-PC-001", "Kaspersky Endpoint", "activa", 180, 20, 45),  # por vencer (≤30 d)
    ("ESPOCH-PC-002", "AutoCAD 2024", "activa", 150, 200, 0),        # vigente
    ("ESPOCH-PC-003", "MATLAB R2024a", "vencida", 400, -10, 0),      # vencida
]


def cargar_demo() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        labs = db.query(Laboratorio).order_by(Laboratorio.id).all()
        if len(labs) < 6:
            print("Faltan laboratorios. Ejecuta primero: python seed.py")
            return

        # Custodios
        custodios = []
        for data in CUSTODIOS:
            c = db.query(Custodio).filter(Custodio.nombre == data["nombre"]).first()
            if not c:
                c = Custodio(**data)
                db.add(c)
                db.commit()
                db.refresh(c)
            custodios.append(c)

        # Usuarios de consulta (decano, DTIC)
        for usr, perfil in [("decano", "consulta"), ("dtic", "consulta")]:
            if not db.query(Usuario).filter(Usuario.usuario == usr).first():
                usuario_service.crear_cuenta(usr, "consulta123", perfil, db=db)

        # Bienes
        for codigo, nombre, tipo, lab_i, cust_i in BIENES:
            if db.get(Bien, codigo) is None:
                bien_service.crear_bien(
                    {
                        "codigo_bien": codigo,
                        "nombre": nombre,
                        "tipo": tipo,
                        "laboratorio_id": labs[lab_i].id,
                        "custodio_id": custodios[cust_i].id,
                    },
                    db=db,
                )

        # Mantenimientos
        for codigo, tipo, dias, obs in MANTENIMIENTOS:
            mantenimiento_service.registrar_mantenimiento(
                codigo_bien=codigo,
                tipo=tipo,
                fecha=_dias(dias),
                observaciones=obs,
                db=db,
            )

        # Software
        for codigo, nombre, lic, inst, venc, scans in SOFTWARE:
            software_service.agregar_software(
                codigo_bien=codigo,
                nombre=nombre,
                licencia=lic,
                fecha_instalacion=_dias(inst),
                vencimiento=_futuro(venc) if venc is not None else None,
                num_escaneos=scans,
                db=db,
            )

        print("Datos de demostración cargados:")
        print(f"  Bienes:         {db.query(Bien).count()}")
        print(f"  Custodios:      {db.query(Custodio).count()}")
        print(f"  Cuentas:        {db.query(Usuario).count()} (admin + decano + dtic)")
        print("  Mantenimientos y software de ejemplo añadidos.")
    finally:
        db.close()


if __name__ == "__main__":
    cargar_demo()
