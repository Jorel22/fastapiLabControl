"""Pruebas de RF-004 — Editar y actualizar registros.

CA-004.1: la edición conserva el histórico y registra la modificación
en la traza de auditoría.
"""
import pytest

from app.models.auditoria import Auditoria
from app.services import bien_service


@pytest.fixture()
def bien(db_session):
    bien_service.crear_bien({"codigo_bien": "PC-1", "nombre": "PC vieja"}, db=db_session)


def test_editar_bien_registra_auditoria(db_session, bien):
    bien_service.actualizar_bien("PC-1", {"nombre": "PC nueva", "tipo": "computadora"}, db=db_session)
    actualizado = bien_service.obtener_bien("PC-1", db=db_session)
    assert actualizado.nombre == "PC nueva"
    assert actualizado.tipo == "computadora"
    # CA-004.1: queda traza de la edición.
    assert db_session.query(Auditoria).filter(Auditoria.entidad == "bienes", Auditoria.operacion == "edicion").count() == 1


def test_editar_sin_cambios_no_audita(db_session, bien):
    """Si no hay cambios reales, no se genera una entrada de auditoría redundante."""
    bien_service.actualizar_bien("PC-1", {"nombre": "PC vieja"}, db=db_session)
    assert db_session.query(Auditoria).filter(Auditoria.operacion == "edicion").count() == 0


def test_editar_bien_inexistente(db_session):
    with pytest.raises(bien_service.BienNoEncontradoError):
        bien_service.actualizar_bien("NO-EXISTE", {"nombre": "X"}, db=db_session)
