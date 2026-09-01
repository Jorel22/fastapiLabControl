"""Pruebas de RF-009 — Generar informes y planes de mantenimiento (CU-005).

CA-009.1: el informe consolida según los filtros.
CA-009.2: un filtro sin registros devuelve informe vacío.
CA-009.3: el perfil de consulta puede generar/ver informes (no modificar).
RD-002 · NFR-006: exportaciones CSV y PDF con nota normativa.
"""
import datetime
import pytest

from app.models.laboratorio import Laboratorio
from app.models.usuario import Usuario
from app.services import bien_service, mantenimiento_service, reporte_service

D_2025A = datetime.date(2025, 3, 10)
D_2025B = datetime.date(2025, 9, 15)


@pytest.fixture()
def datos(db_session):
    """Dos laboratorios con mantenimientos en distintos semestres."""
    lab1 = Laboratorio(nombre="Lab 1")
    lab2 = Laboratorio(nombre="Lab 2")
    db_session.add_all([lab1, lab2])
    db_session.commit()
    bien_service.crear_bien({"codigo_bien": "A-1", "nombre": "PC", "laboratorio_id": lab1.id}, db=db_session)
    bien_service.crear_bien({"codigo_bien": "B-1", "nombre": "Switch", "laboratorio_id": lab2.id}, db=db_session)
    mantenimiento_service.registrar_mantenimiento("A-1", "preventivo", D_2025A, db=db_session)
    mantenimiento_service.registrar_mantenimiento("A-1", "correctivo", D_2025B, db=db_session)
    mantenimiento_service.registrar_mantenimiento("B-1", "preventivo", D_2025B, db=db_session)
    return {"lab1": lab1.id, "lab2": lab2.id}


def test_reporte_sin_filtros(db_session, datos):
    assert len(reporte_service.generar_reporte(db=db_session)) == 3


def test_filtro_por_semestre(db_session, datos):
    """CA-009.1: el semestre acota por rango de fechas."""
    assert len(reporte_service.generar_reporte(semestre="2025-A", db=db_session)) == 1
    assert len(reporte_service.generar_reporte(semestre="2025-B", db=db_session)) == 2


def test_filtro_por_laboratorio_y_tipo(db_session, datos):
    assert len(reporte_service.generar_reporte(laboratorio_id=datos["lab1"], db=db_session)) == 2
    assert len(reporte_service.generar_reporte(tipo="correctivo", db=db_session)) == 1


def test_filtro_por_equipo(db_session, datos):
    assert len(reporte_service.generar_reporte(codigo_bien="B-1", db=db_session)) == 1


def test_filtro_sin_registros(db_session, datos):
    """CA-009.2: combinación sin coincidencias -> informe vacío."""
    assert reporte_service.generar_reporte(semestre="2030-A", db=db_session) == []


def test_export_csv_contiene_nota_y_datos(db_session, datos):
    reporte = reporte_service.generar_reporte(db=db_session)
    csv_str = reporte_service.exportar_csv(reporte)
    assert "Normas de Control Interno" in csv_str  # NFR-006
    assert "A-1" in csv_str


def test_export_pdf_genera_bytes(db_session, datos):
    reporte = reporte_service.generar_reporte(db=db_session)
    pdf = reporte_service.exportar_pdf(reporte)
    assert pdf[:4] == b"%PDF"  # firma de archivo PDF


# --- Capa web ------------------------------------------------------------
def _crear_login(client, db_session, perfil):
    u = Usuario(usuario="u_" + perfil, perfil=perfil, activo=True)
    u.set_password("c")
    db_session.add(u)
    db_session.commit()
    client.post("/api/auth/login", json={"usuario": "u_" + perfil, "password": "c"})


def test_consulta_puede_ver_reportes(client, db_session, datos):
    """CA-009.3: el perfil consulta accede a los informes."""
    _crear_login(client, db_session, "consulta")
    resp = client.get("/api/reportes")
    assert resp.status_code == 200


def test_export_pdf_web(client, db_session, datos):
    _crear_login(client, db_session, "administrador")
    resp = client.get("/api/reportes?formato=pdf")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/pdf"


def test_export_csv_web(client, db_session, datos):
    _crear_login(client, db_session, "administrador")
    resp = client.get("/api/reportes?formato=csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["Content-Type"]
