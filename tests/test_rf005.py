"""Pruebas de RF-005 — Gestionar cuentas de consulta.

CA-005.1: el administrador crea, desactiva/activa y restablece
credenciales de las cuentas de consulta.
"""
import pytest

from app.services import usuario_service


def test_crear_cuenta_consulta(db_session):
    u = usuario_service.crear_cuenta("decano", "clave123", "consulta", db=db_session)
    assert u.id is not None
    assert u.perfil == "consulta"
    assert u.check_password("clave123")


def test_no_duplicar_usuario(db_session):
    usuario_service.crear_cuenta("dtic", "clave123", db=db_session)
    with pytest.raises(usuario_service.UsuarioDuplicadoError):
        usuario_service.crear_cuenta("dtic", "otra123", db=db_session)


def test_desactivar_y_activar(db_session):
    u = usuario_service.crear_cuenta("decano", "clave123", db=db_session)
    usuario_service.cambiar_estado(u.id, False, db=db_session)
    assert usuario_service.obtener_usuario(u.id, db=db_session).activo is False
    usuario_service.cambiar_estado(u.id, True, db=db_session)
    assert usuario_service.obtener_usuario(u.id, db=db_session).activo is True


def test_restablecer_password(db_session):
    u = usuario_service.crear_cuenta("decano", "clave123", db=db_session)
    usuario_service.restablecer_password(u.id, "nueva456", db=db_session)
    actualizado = usuario_service.obtener_usuario(u.id, db=db_session)
    assert actualizado.check_password("nueva456")
    assert not actualizado.check_password("clave123")


def test_consulta_no_accede_a_gestion_cuentas(client, db_session):
    """Solo el administrador gestiona cuentas (CA-001.3)."""
    usuario_service.crear_cuenta("decano", "clave123", "consulta", db=db_session)
    client.post("/api/auth/login", json={"usuario": "decano", "password": "clave123"})
    assert client.get("/api/usuarios").status_code == 403
