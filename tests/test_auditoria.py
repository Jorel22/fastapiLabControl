"""Pruebas del servicio de auditoría (NFR-003 · RD-003)."""
from app.models.auditoria import Auditoria
from app.models.usuario import Usuario
from app.services.auditoria import registrar_auditoria


def test_registrar_auditoria_crea_entrada(db_session):
    u = Usuario(usuario="tecnico", perfil="administrador")
    u.set_password("x")
    db_session.add(u)
    db_session.commit()

    registrar_auditoria(
        entidad="bienes",
        operacion="alta",
        registro_id="ESPOCH-001",
        detalle={"nombre": "PC Dell"},
        usuario_id=u.id,
        commit=True,
        db=db_session,
    )

    entradas = db_session.query(Auditoria).all()
    assert len(entradas) == 1
    assert entradas[0].entidad == "bienes"
    assert entradas[0].operacion == "alta"
    assert entradas[0].usuario_id == u.id
    assert "PC Dell" in entradas[0].detalle
