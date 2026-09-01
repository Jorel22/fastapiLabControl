"""Pruebas de RF-003 — Registrar mantenimiento preventivo/correctivo (CU-003).

CA-003.1: registro válido se incorpora al histórico.
CA-003.2: tipo obligatorio.
CA-003.3: fecha no posterior a la actual.
CA-003.4: el correctivo permite detallar componentes (observaciones).
"""
import datetime
import pytest

from app.models.auditoria import Auditoria
from app.models.mantenimiento import Mantenimiento
from app.services import bien_service, mantenimiento_service

HOY = datetime.date.today()
MANANA = HOY + datetime.timedelta(days=1)


@pytest.fixture()
def bien(db_session):
    bien_service.crear_bien({"codigo_bien": "B-1", "nombre": "PC"}, db=db_session)


def test_registro_valido_va_al_historico(db_session, bien):
    m = mantenimiento_service.registrar_mantenimiento(
        "B-1", "preventivo", HOY, "Limpieza general", db=db_session
    )
    assert m.id is not None
    assert db_session.query(Mantenimiento).filter(Mantenimiento.codigo_bien == "B-1").count() == 1
    assert db_session.query(Auditoria).filter(Auditoria.entidad == "mantenimientos").count() == 1


def test_tipo_obligatorio(db_session, bien):
    """CA-003.2: un tipo vacío o inválido se rechaza."""
    with pytest.raises(mantenimiento_service.TipoInvalidoError):
        mantenimiento_service.registrar_mantenimiento("B-1", "", HOY, db=db_session)


def test_fecha_futura_rechazada(db_session, bien):
    """CA-003.3: la fecha no puede ser posterior a hoy."""
    with pytest.raises(mantenimiento_service.FechaFuturaError):
        mantenimiento_service.registrar_mantenimiento("B-1", "correctivo", MANANA, db=db_session)


def test_correctivo_con_componentes(db_session, bien):
    """CA-003.4: el correctivo guarda el detalle de componentes."""
    m = mantenimiento_service.registrar_mantenimiento(
        "B-1", "correctivo", HOY, "Se sustituyó HDD por SSD", db=db_session
    )
    assert "SSD" in m.observaciones


def test_mantenimiento_sobre_bien_inexistente(db_session):
    with pytest.raises(bien_service.BienNoEncontradoError):
        mantenimiento_service.registrar_mantenimiento("NO-EXISTE", "preventivo", HOY, db=db_session)
