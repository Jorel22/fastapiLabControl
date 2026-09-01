"""Pruebas de RF-001 — Autenticación y control de acceso (JWT)."""
import pytest
from fastapi import Depends
from fastapi.responses import PlainTextResponse

from app.core.security import require_admin
from app.models.usuario import Usuario
from app.routers.auth import ERROR_GENERICO


@pytest.fixture()
def usuarios(db_session):
    """Crea un administrador y un usuario de consulta."""
    admin = Usuario(usuario="tecnico", perfil="administrador", activo=True)
    admin.set_password("clave-admin")
    consulta = Usuario(usuario="decano", perfil="consulta", activo=True)
    consulta.set_password("clave-consulta")
    inactivo = Usuario(usuario="baja", perfil="consulta", activo=False)
    inactivo.set_password("clave-baja")
    db_session.add_all([admin, consulta, inactivo])
    db_session.commit()


def _login(client, usuario, password):
    return client.post(
        "/api/auth/login",
        json={"usuario": usuario, "password": password},
    )


# --- CA-001.1 -------------------------------------------------------------
def test_login_exitoso_admin(client, usuarios):
    resp = _login(client, "tecnico", "clave-admin")
    assert resp.status_code == 200
    # La sesión queda activa mediante cookies: una ruta protegida responde 200.
    assert client.get("/api/auth/perfil").status_code == 200


# --- CA-001.2 -------------------------------------------------------------
def test_login_password_incorrecta_mensaje_generico(client, usuarios):
    resp = _login(client, "tecnico", "incorrecta")
    assert resp.status_code == 401
    assert resp.json()["error"] == ERROR_GENERICO


def test_login_usuario_inexistente_mismo_mensaje(client, usuarios):
    """No debe revelarse si el fallo fue por usuario o por contraseña."""
    resp = _login(client, "noexiste", "loquesea")
    assert resp.status_code == 401
    assert resp.json()["error"] == ERROR_GENERICO


def test_cuenta_inactiva_no_inicia_sesion(client, usuarios):
    """Una cuenta desactivada (RF-005) no puede entrar; mensaje genérico."""
    resp = _login(client, "baja", "clave-baja")
    assert resp.status_code == 401
    assert resp.json()["error"] == ERROR_GENERICO


# --- CA-001.3 -------------------------------------------------------------
def _registrar_ruta_admin(app):
    """Registra una ruta protegida por require_admin para la prueba."""
    @app.get("/_solo_admin")
    def _solo_admin(current_user=Depends(require_admin)):
        return PlainTextResponse("ok-admin")


def test_consulta_no_accede_ruta_admin(app, client, usuarios):
    _registrar_ruta_admin(app)
    _login(client, "decano", "clave-consulta")  # perfil consulta
    resp = client.get("/_solo_admin")
    assert resp.status_code == 403  # autenticado pero sin permiso


def test_admin_si_accede_ruta_admin(app, client, usuarios):
    _registrar_ruta_admin(app)
    _login(client, "tecnico", "clave-admin")
    resp = client.get("/_solo_admin")
    assert resp.status_code == 200
    assert "ok-admin" in resp.text


# --- Logout ---------------------------------------------------------------
def test_logout_cierra_sesion(client, usuarios):
    _login(client, "tecnico", "clave-admin")
    assert client.get("/api/auth/perfil").status_code == 200
    client.post("/api/auth/logout")
    # Tras cerrar sesión, la ruta protegida devuelve 401.
    resp = client.get("/api/auth/perfil")
    assert resp.status_code == 401
