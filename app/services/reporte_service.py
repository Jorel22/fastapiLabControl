"""Servicio de informes y planes de mantenimiento (RF-009 · RD-002 · NFR-006).

Genera reportes consolidados de mantenimientos filtrables por semestre,
laboratorio, tipo de mantenimiento o equipo, y los exporta a CSV y PDF
con el encabezado de conformidad normativa (Normas de Control Interno
series 406/410 y Políticas DTIC-ESPOCH).
"""
import csv
import datetime
import io
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.bien import Bien
from app.models.laboratorio import Laboratorio
from app.models.mantenimiento import Mantenimiento

# Texto de conformidad incluido en los reportes (NFR-006 · RD-002).
NOTA_NORMATIVA = (
    "Reporte generado conforme a las Normas de Control Interno (series 406 y 410) "
    "y las Políticas de Mantenimiento Preventivo y Correctivo de la DTIC-ESPOCH."
)

ENCABEZADOS = [
    "Código del bien",
    "Equipo",
    "Laboratorio",
    "Tipo",
    "Fecha",
    "Observaciones",
    "Registrado por",
]


def _rango_semestre(semestre: Optional[str]):
    """Convierte 'YYYY-A' (ene–jun) o 'YYYY-B' (jul–dic) en (inicio, fin)."""
    if not semestre:
        return None, None
    try:
        anio_str, periodo = semestre.split("-")
        anio = int(anio_str)
    except (ValueError, AttributeError):
        return None, None
    if periodo.upper() == "A":
        return datetime.date(anio, 1, 1), datetime.date(anio, 6, 30)
    if periodo.upper() == "B":
        return datetime.date(anio, 7, 1), datetime.date(anio, 12, 31)
    return None, None


def semestres_disponibles(db: Optional[Session] = None) -> list:
    """Devuelve los semestres con mantenimientos registrados (orden desc.)."""
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        fechas = [m[0] for m in db.query(Mantenimiento.fecha).all()]
        etiquetas = set()
        for f in fechas:
            if f:
                periodo = "A" if f.month <= 6 else "B"
                etiquetas.add(f"{f.year}-{periodo}")
        return sorted(etiquetas, reverse=True)
    finally:
        if session_created:
            db.close()


def generar_reporte(
    semestre: Optional[str] = None,
    laboratorio_id: Optional[int] = None,
    tipo: Optional[str] = None,
    codigo_bien: Optional[str] = None,
    db: Optional[Session] = None,
) -> list:
    """Devuelve los mantenimientos que cumplen los filtros (RF-009 · CA-009.1)."""
    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        query = db.query(Mantenimiento).join(Bien, Mantenimiento.codigo_bien == Bien.codigo_bien)

        inicio, fin = _rango_semestre(semestre)
        if inicio and fin:
            query = query.filter(Mantenimiento.fecha >= inicio, Mantenimiento.fecha <= fin)
        if laboratorio_id:
            query = query.filter(Bien.laboratorio_id == laboratorio_id)
        if tipo:
            query = query.filter(Mantenimiento.tipo == tipo)
        if codigo_bien:
            query = query.filter(Mantenimiento.codigo_bien == codigo_bien)

        return query.order_by(Mantenimiento.fecha.asc(), Mantenimiento.id.asc()).all()
    finally:
        if session_created:
            db.close()


def _filas(reporte: list) -> list:
    """Aplana los mantenimientos a filas para CSV/PDF."""
    filas = []
    for m in reporte:
        filas.append(
            [
                m.codigo_bien,
                m.bien.nombre if m.bien else "",
                m.bien.laboratorio.nombre if m.bien and m.bien.laboratorio else "",
                m.tipo,
                m.fecha.strftime("%Y-%m-%d") if m.fecha else "",
                m.observaciones or "",
                m.usuario.usuario if m.usuario else "",
            ]
        )
    return filas


def exportar_csv(reporte: list) -> str:
    """Genera el contenido CSV del reporte (incluye nota normativa)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([NOTA_NORMATIVA])
    writer.writerow([f"Generado: {datetime.date.today().isoformat()}"])
    writer.writerow([])
    writer.writerow(ENCABEZADOS)
    writer.writerows(_filas(reporte))
    return buffer.getvalue()


def exportar_pdf(reporte: list, titulo: str = "Informe de Mantenimientos") -> bytes:
    """Genera el reporte en PDF con ReportLab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph("LabControl Mecánica ESPOCH", estilos["Title"]),
        Paragraph(titulo, estilos["Heading2"]),
        Paragraph(f"Generado: {datetime.date.today().isoformat()}", estilos["Normal"]),
        Spacer(1, 6 * mm),
    ]

    datos = [ENCABEZADOS] + _filas(reporte)
    tabla = Table(datos, repeatRows=1)
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elementos.append(tabla)
    elementos.append(Spacer(1, 8 * mm))
    elementos.append(Paragraph(NOTA_NORMATIVA, estilos["Italic"]))

    doc.build(elementos)
    return buffer.getvalue()
