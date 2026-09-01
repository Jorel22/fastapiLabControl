"""Pruebas de RF-006 — Consultar histórico técnico por código del bien (CU-004).

CA-006.1: muestra las intervenciones en orden cronológico.
CA-006.2: código inexistente -> no se encuentra el equipo.
CA-006.3: equipo sin mantenimientos -> histórico vacío.
"""
import datetime
import pytest

from app.models.usuario import Usuario
from app.services import bien_service, mantenimiento_service

D1 = datetime.date(2025, 1, 10)
D2 = datetime.date(2025, 6, 20)
D3 = datetime.date(2026, 2, 5)


def test_historico_orden_cronologico(db_session):
    """CA-006.1: las intervenciones se devuelven de la más antigua a la más reciente."""
    bien_service.crear_bien({"codigo_bien": "B-1", "nombre": "PC"}, db=db_session)
    # Se insertan desordenadas a propósito.
    mantenimiento_service.registrar_mantenimiento("B-1", "preventivo", D2, db=db_session)
    mantenimiento_service.registrar_mantenimiento("B-1", "correctivo", D1, db=db_session)
    mantenimiento_service.registrar_mantenimiento("B-1", "preventivo", D3, db=db_session)

    bien, registros = mantenimiento_service.obtener_historico("B-1", db=db_session)
    fechas = [m.fecha for m in registros]
    assert fechas == [D1, D2, D3]  # orden ascendente


def test_codigo_inexistente(db_session):
    """CA-006.2: consultar un código que no existe lanza el error correspondiente."""
    with pytest.raises(bien_service.BienNoEncontradoError):
        mantenimiento_service.obtener_historico("NO-EXISTE", db=db_session)


def test_equipo_sin_mantenimientos(db_session):
    """CA-006.3: un equipo sin mantenimientos devuelve histórico vacío."""
    bien_service.crear_bien({"codigo_bien": "B-2", "nombre": "Switch"}, db=db_session)
    bien, registros = mantenimiento_service.obtener_historico("B-2", db=db_session)
    assert bien.codigo_bien == "B-2"
    assert registros == []


def test_historico_web_codigo_inexistente_404(client, db_session):
    """La ruta web responde 404 con aviso cuando el código no existe."""
    u = Usuario(usuario="decano", perfil="consulta", activo=True)
    u.set_password("c")
    db_session.add(u)
    db_session.commit()

    client.post("/api/auth/login", json={"usuario": "decano", "password": "c"})
    resp = client.get("/api/bienes/NO-EXISTE/historico")
    assert resp.status_code == 404


def test_historico_web_consulta_puede_ver(client, db_session):
    """El perfil de consulta (decano/DTIC) puede ver el histórico (solo lectura)."""
    bien_service.crear_bien({"codigo_bien": "B-3", "nombre": "PC"}, db=db_session)
    mantenimiento_service.registrar_mantenimiento("B-3", "preventivo", D1, db=db_session)
    u = Usuario(usuario="dtic", perfil="consulta", activo=True)
    u.set_password("c")
    db_session.add(u)
    db_session.commit()

    client.post("/api/auth/login", json={"usuario": "dtic", "password": "c"})
    resp = client.get("/api/bienes/B-3/historico")
    assert resp.status_code == 200
    assert resp.json()["bien"]["codigo_bien"] == "B-3"
