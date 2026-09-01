"""Router de informes y planes de mantenimiento (API REST)."""
from typing import Optional
from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.laboratorio import Laboratorio
from app.models.mantenimiento import TIPOS
from app.models.usuario import Usuario
from app.services import reporte_service

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])


@router.get("")
def index(
    semestre: Optional[str] = None,
    laboratorio_id: Optional[int] = None,
    tipo: Optional[str] = None,
    codigo_bien: Optional[str] = None,
    formato: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Genera el informe según los filtros y, opcionalmente, lo exporta a CSV o PDF."""
    reporte = reporte_service.generar_reporte(
        semestre=semestre,
        laboratorio_id=laboratorio_id,
        tipo=tipo,
        codigo_bien=codigo_bien,
        db=db,
    )

    # Exportaciones (CSV / PDF)
    if formato == "csv":
        contenido = reporte_service.exportar_csv(reporte)
        return Response(
            content=contenido,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=reporte_mantenimientos.csv"},
        )

    if formato == "pdf":
        contenido = reporte_service.exportar_pdf(reporte)
        return Response(
            content=contenido,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=reporte_mantenimientos.pdf"},
        )

    # Si no pide formato de archivo, devuelve los datos en JSON
    labs = db.query(Laboratorio).order_by(Laboratorio.nombre).all()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "reporte": [m.to_dict() for m in reporte],
            "catalogos": {
                "laboratorios": [l.to_dict() for l in labs],
                "tipos": list(TIPOS),
                "semestres": reporte_service.semestres_disponibles(db=db),
            },
        },
    )
