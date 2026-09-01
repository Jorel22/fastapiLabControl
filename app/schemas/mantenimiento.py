"""Esquemas Pydantic para mantenimientos."""
from typing import Any, List, Optional
from pydantic import BaseModel, Field
from app.schemas.bien import BienResponse


class MantenimientoCreate(BaseModel):
    tipo: Optional[str] = Field(None, description="Tipo: preventivo o correctivo", examples=["preventivo"])
    fecha: Optional[str] = Field(None, description="Fecha de ejecución en formato YYYY-MM-DD", examples=["2026-08-31"])
    observaciones: Optional[str] = Field(None, description="Detalle u observaciones del mantenimiento")


class MantenimientoResponse(BaseModel):
    id: int
    codigo_bien: str
    tipo: str
    fecha: Optional[str] = None
    observaciones: Optional[str] = None
    usuario_id: Optional[int] = None
    usuario: Optional[str] = None


class HistoricoResponse(BaseModel):
    bien: BienResponse
    registros: List[MantenimientoResponse]
