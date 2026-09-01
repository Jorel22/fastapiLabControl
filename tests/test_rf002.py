"""Pruebas de RF-002 — Registrar inventario de bienes (CU-002).

CA-002.1: alta válida almacena el bien.
CA-002.2: sin código del bien -> no se guarda.
CA-002.3: código duplicado -> se rechaza.
"""
import pytest

from app.models.auditoria import Auditoria
from app.models.bien import Bien
from app.models.usuario import Usuario
from app.services import bien_service


@pytest.fixture()
def admin(db_session):
    u = Usuario(usuario="tecnico", perfil="administrador", activo=True)
    u.set_password("clave")
    db_session.add(u)
    db_session.commit()


def _login(client):
    client.post("/api/auth/login", json={"usuario": "tecnico", "password": "clave"})


# --- Capa de servicio ----------------------------------------------------
def test_crear_bien_valido(db_session):
    bien = bien_service.crear_bien({"codigo_bien": "ESPOCH-001", "nombre": "PC"}, db=db_session)
    assert bien.codigo_bien == "ESPOCH-001"
    assert bien.estado == "activo"
    # CA-002.1: se registra y queda traza de auditoría (NFR-003).
    assert db_session.get(Bien, "ESPOCH-001") is not None
    assert db_session.query(Auditoria).filter(Auditoria.operacion == "alta").count() == 1


def test_codigo_requerido(db_session):
    """CA-002.2: el código del bien es obligatorio."""
    with pytest.raises(bien_service.CodigoRequeridoError):
        bien_service.crear_bien({"codigo_bien": "  ", "nombre": "PC"}, db=db_session)


def test_codigo_duplicado(db_session):
    """CA-002.3: no se permite duplicar el código del bien."""
    bien_service.crear_bien({"codigo_bien": "DUP-1", "nombre": "A"}, db=db_session)
    with pytest.raises(bien_service.CodigoDuplicadoError):
        bien_service.crear_bien({"codigo_bien": "DUP-1", "nombre": "B"}, db=db_session)


# --- Capa web ------------------------------------------------------------
def test_alta_via_web_admin(client, admin):
    _login(client)
    resp = client.post(
        "/api/bienes",
        json={"codigo_bien": "WEB-1", "nombre": "Equipo Web", "laboratorio_id": 0,
              "custodio_id": 0, "tipo": ""},
    )
    assert resp.status_code == 201  # creado


def test_alta_duplicada_via_web_devuelve_409(client, admin):
    _login(client)
    data = {"codigo_bien": "WEB-2", "nombre": "X", "laboratorio_id": 0,
            "custodio_id": 0, "tipo": ""}
    client.post("/api/bienes", json=data)
    resp = client.post("/api/bienes", json=data)
    assert resp.status_code == 409  # CA-002.3


def test_consulta_no_puede_crear(client, db_session):
    """El perfil de consulta no accede al alta (CA-001.3)."""
    u = Usuario(usuario="decano", perfil="consulta", activo=True)
    u.set_password("c")
    db_session.add(u)
    db_session.commit()

    client.post("/api/auth/login", json={"usuario": "decano", "password": "c"})
    resp = client.post("/api/bienes", json={"codigo_bien": "WEB-3", "nombre": "PC"})
    assert resp.status_code == 403
