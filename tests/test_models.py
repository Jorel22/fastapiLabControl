"""Pruebas del modelo de datos.

Verifican que las 7 entidades, sus relaciones y las restricciones de
dominio funcionan según el ER del SRS (§5.2).
"""
import datetime
import pytest

from app.models.auditoria import Auditoria
from app.models.bien import Bien
from app.models.custodio import Custodio
from app.models.laboratorio import Laboratorio
from app.models.mantenimiento import Mantenimiento
from app.models.software import Software
from app.models.usuario import Usuario


def test_crear_entidades_y_relaciones(db_session):
    """Crea un grafo completo y verifica las relaciones del dominio."""
    lab = Laboratorio(nombre="Laboratorio 1", ubicacion="Mecánica")
    cust = Custodio(nombre="Ana Pérez", cargo="Técnico")
    user = Usuario(usuario="tecnico", perfil="administrador")
    user.set_password("secreta")
    db_session.add_all([lab, cust, user])
    db_session.commit()

    bien = Bien(
        codigo_bien="ESPOCH-001",
        nombre="PC Dell",
        laboratorio=lab,
        custodio=cust,
    )
    db_session.add(bien)
    db_session.commit()

    mant = Mantenimiento(
        codigo_bien="ESPOCH-001",
        tipo="preventivo",
        fecha=datetime.date.today(),
        observaciones="Limpieza",
        usuario=user,
    )
    sw = Software(codigo_bien="ESPOCH-001", nombre="Windows 11", licencia="activa")
    db_session.add_all([mant, sw])
    db_session.commit()

    # Relaciones bidireccionales (ER §5.2).
    assert bien in lab.bienes
    assert bien in cust.bienes
    assert mant in bien.mantenimientos
    assert sw in bien.software
    assert mant in user.mantenimientos
    assert mant.bien.codigo_bien == "ESPOCH-001"


def test_password_hash(db_session):
    """La contraseña se guarda hasheada y se verifica (NFR-003)."""
    u = Usuario(usuario="x", perfil="consulta")
    u.set_password("clave123")
    assert u.password_hash != "clave123"
    assert u.check_password("clave123")
    assert not u.check_password("incorrecta")


def test_codigo_bien_pk_rechaza_duplicado(db_session):
    """El código del bien es PK: rechaza duplicados (CA-002.3)."""
    db_session.add(Bien(codigo_bien="DUP-1", nombre="A"))
    db_session.commit()
    db_session.add(Bien(codigo_bien="DUP-1", nombre="B"))
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()


def test_check_constraint_estado_invalido(db_session):
    """SQLite rechaza un estado fuera del dominio permitido."""
    db_session.add(Bien(codigo_bien="E-1", nombre="X", estado="inexistente"))
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()


def test_baja_logica_conserva_historico(db_session):
    """Dar de baja cambia el estado sin borrar el bien (RF-008)."""
    b = Bien(codigo_bien="B-1", nombre="Equipo", estado="activo")
    db_session.add(b)
    db_session.commit()
    b.estado = "dado_de_baja"
    db_session.commit()
    recuperado = db_session.get(Bien, "B-1")
    assert recuperado is not None
    assert recuperado.estado == "dado_de_baja"
    assert not recuperado.esta_activo


def test_auditoria_registra_operacion(db_session):
    """La tabla de auditoría almacena operaciones (NFR-003 / RD-003)."""
    u = Usuario(usuario="aud", perfil="administrador")
    u.set_password("x")
    db_session.add(u)
    db_session.commit()
    a = Auditoria(
        usuario=u, entidad="bienes", operacion="alta", registro_id="ESPOCH-001"
    )
    db_session.add(a)
    db_session.commit()
    assert db_session.query(Auditoria).count() == 1
