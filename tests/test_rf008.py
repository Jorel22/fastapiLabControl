"""Pruebas de RF-008 — Dar de baja y reactivar equipos.

CA-008.1: la baja es lógica y conserva el histórico.
CA-008.2: un bien dado de baja se puede reactivar; queda en auditoría.
RF-011 (CA-011.1): filtros del listado.
"""
from app.models.auditoria import Auditoria
from app.models.bien import Bien
from app.models.laboratorio import Laboratorio
from app.services import bien_service
import pytest


def test_baja_es_logica_y_conserva_bien(db_session):
    bien_service.crear_bien({"codigo_bien": "B-1", "nombre": "Equipo"}, db=db_session)
    bien_service.dar_de_baja("B-1", db=db_session)
    bien = db_session.get(Bien, "B-1")
    assert bien is not None  # no se borra (CA-008.1)
    assert bien.estado == "dado_de_baja"
    assert db_session.query(Auditoria).filter(Auditoria.operacion == "baja").count() == 1


def test_reactivar(db_session):
    bien_service.crear_bien({"codigo_bien": "B-2", "nombre": "Equipo"}, db=db_session)
    bien_service.dar_de_baja("B-2", db=db_session)
    bien_service.reactivar("B-2", db=db_session)
    assert db_session.get(Bien, "B-2").estado == "activo"
    assert db_session.query(Auditoria).filter(Auditoria.operacion == "reactivacion").count() == 1


def test_baja_bien_inexistente(db_session):
    with pytest.raises(bien_service.BienNoEncontradoError):
        bien_service.dar_de_baja("NO-EXISTE", db=db_session)


def test_filtros_listado(db_session):
    """RF-011 · CA-011.1: filtrar por laboratorio, tipo y estado."""
    lab = Laboratorio(nombre="Lab 1")
    db_session.add(lab)
    db_session.commit()
    bien_service.crear_bien(
        {"codigo_bien": "A", "nombre": "PC", "tipo": "computadora",
         "laboratorio_id": lab.id}, db=db_session
    )
    bien_service.crear_bien(
        {"codigo_bien": "B", "nombre": "Switch", "tipo": "switch",
         "laboratorio_id": lab.id}, db=db_session
    )
    bien_service.dar_de_baja("B", db=db_session)

    assert len(bien_service.listar_bienes(tipo="computadora", db=db_session)) == 1
    assert len(bien_service.listar_bienes(estado="dado_de_baja", db=db_session)) == 1
    assert len(bien_service.listar_bienes(laboratorio_id=lab.id, db=db_session)) == 2
    assert len(bien_service.listar_bienes(db=db_session)) == 2
