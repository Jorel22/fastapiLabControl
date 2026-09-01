"""Pruebas de requisitos no funcionales críticos.

NFR-001: el histórico de un equipo con hasta 200 registros se consulta
         en ≤3 segundos.
NFR-003: toda operación de escritura queda registrada en la traza de
         auditoría.
"""
import datetime
import time

from app.models.auditoria import Auditoria
from app.models.mantenimiento import Mantenimiento
from app.services import bien_service, mantenimiento_service

HOY = datetime.date.today()


def test_nfr001_historico_200_registros_bajo_3s(db_session):
    """NFR-001: rendimiento de la consulta del histórico."""
    bien_service.crear_bien({"codigo_bien": "PERF-1", "nombre": "PC"}, db=db_session)
    # Inserción masiva de 200 mantenimientos.
    for i in range(200):
        db_session.add(
            Mantenimiento(
                codigo_bien="PERF-1",
                tipo="preventivo" if i % 2 == 0 else "correctivo",
                fecha=HOY - datetime.timedelta(days=i),
                observaciones=f"Intervención {i}",
            )
        )
    db_session.commit()

    inicio = time.perf_counter()
    _, registros = mantenimiento_service.obtener_historico("PERF-1", db=db_session)
    duracion = time.perf_counter() - inicio

    assert len(registros) == 200
    assert duracion < 3.0  # NFR-001


def test_nfr003_auditoria_de_escrituras(db_session):
    """NFR-003: alta, edición y baja generan traza de auditoría."""
    bien_service.crear_bien({"codigo_bien": "AUD-1", "nombre": "PC"}, db=db_session)
    bien_service.actualizar_bien("AUD-1", {"nombre": "PC editada"}, db=db_session)
    bien_service.dar_de_baja("AUD-1", db=db_session)

    operaciones = {a.operacion for a in db_session.query(Auditoria).all()}
    assert {"alta", "edicion", "baja"}.issubset(operaciones)
    # Cada entrada identifica la entidad afectada.
    assert all(a.entidad for a in db_session.query(Auditoria).all())
