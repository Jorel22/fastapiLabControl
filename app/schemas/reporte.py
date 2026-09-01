"""Esquemas Pydantic para reportes."""
from typing import Any, List
from pydantic import BaseModel
from app.schemas.mantenimiento import MantenimientoResponse


class ReporteCatalogosResponse(BaseModel):
    laboratorios: List[Any]
    tipos: List[str]
    semestres: List[str]


class ReporteResponse(BaseModel):
    reporte: List[MantenimientoResponse]
    catalogos: ReporteCatalogosResponse
