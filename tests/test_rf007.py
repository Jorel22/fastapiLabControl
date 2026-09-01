"""Pruebas de RF-007 — Controlar software y licencias.

CA-007.1: registrar software de un equipo.
CA-007.2: señalar licencias próximas a vencer / vencidas.
"""
import datetime
import pytest

from app.models.auditoria import Auditoria
from app.models.software import Software
from app.services import bien_service, software_service

HOY = datetime.date.today()


@pytest.fixture()
def bien(db_session):
    bien_service.crear_bien({"codigo_bien": "PC-1", "nombre": "PC"}, db=db_session)


def test_agregar_software(db_session, bien):
    sw = software_service.agregar_software("PC-1", "Windows 11", num_escaneos=3, db=db_session)
    assert sw.id is not None
    assert db_session.query(Software).filter(Software.codigo_bien == "PC-1").count() == 1
    assert db_session.query(Auditoria).filter(Auditoria.entidad == "software").count() == 1


def test_nombre_obligatorio(db_session, bien):
    with pytest.raises(software_service.NombreSoftwareRequeridoError):
        software_service.agregar_software("PC-1", "  ", db=db_session)


def test_estado_licencia_vigente_por_vencer_vencida(db_session, bien):
    """CA-007.2: el estado se calcula según la fecha de vencimiento."""
    vigente = software_service.agregar_software(
        "PC-1", "Office", vencimiento=HOY + datetime.timedelta(days=200), db=db_session
    )
    por_vencer = software_service.agregar_software(
        "PC-1", "Kaspersky", vencimiento=HOY + datetime.timedelta(days=10), db=db_session
    )
    vencida = software_service.agregar_software(
        "PC-1", "AutoCAD", vencimiento=HOY - datetime.timedelta(days=5), db=db_session
    )
    assert vigente.estado_licencia == "vigente"
    assert por_vencer.estado_licencia == "por_vencer"
    assert vencida.estado_licencia == "vencida"
