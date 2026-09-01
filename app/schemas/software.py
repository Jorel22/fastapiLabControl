"""Esquemas Pydantic para software y licencias."""
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.bien import BienResponse


class SoftwareCreate(BaseModel):
    nombre: Optional[str] = Field(None, description="Nombre del software o programa", examples=["AutoCAD 2024"])
    licencia: Optional[str] = Field("activa", description="Estado de la licencia: activa o vencida", examples=["activa"])
    fecha_instalacion: Optional[str] = Field(None, description="Fecha de instalación en formato YYYY-MM-DD")
    vencimiento: Optional[str] = Field(None, description="Fecha de vencimiento en formato YYYY-MM-DD")
    num_escaneos: Optional[int] = Field(0, description="Número de escaneos (antivirus)", examples=[0])


class SoftwareResponse(BaseModel):
    id: int
    codigo_bien: str
    nombre: str
    licencia: Optional[str] = None
    fecha_instalacion: Optional[str] = None
    vencimiento: Optional[str] = None
    num_escaneos: Optional[int] = 0
    estado_licencia: Optional[str] = None
    dias_para_vencer: Optional[int] = None


class BienSoftwareListResponse(BaseModel):
    bien: BienResponse
    softwares: List[SoftwareResponse]
