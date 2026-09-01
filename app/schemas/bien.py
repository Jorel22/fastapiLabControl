"""Esquemas Pydantic para inventario de bienes."""
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class BienCreate(BaseModel):
    codigo_bien: Optional[str] = Field(None, description="Código único del bien", examples=["ESPOCH-PC-001"])
    nombre: Optional[str] = Field(None, description="Nombre del equipo", examples=["PC Dell OptiPlex 7090"])
    numero_serie: Optional[str] = Field(None, description="Número de serie", examples=["SN12345678"])
    descripcion: Optional[str] = Field(None, description="Descripción técnica")
    tipo: Optional[str] = Field(None, description="Tipo de equipo (computadora, switch, etc.)", examples=["computadora"])
    laboratorio_id: Optional[Union[int, str]] = Field(None, description="ID del laboratorio")
    custodio_id: Optional[Union[int, str]] = Field(None, description="ID del custodio")


class BienUpdate(BaseModel):
    nombre: Optional[str] = Field(None, description="Nombre del equipo")
    numero_serie: Optional[str] = Field(None, description="Número de serie")
    descripcion: Optional[str] = Field(None, description="Descripción técnica")
    tipo: Optional[str] = Field(None, description="Tipo de equipo")
    laboratorio_id: Optional[Union[int, str]] = Field(None, description="ID del laboratorio")
    custodio_id: Optional[Union[int, str]] = Field(None, description="ID del custodio")


class BienResponse(BaseModel):
    codigo_bien: str
    numero_serie: Optional[str] = None
    nombre: str
    descripcion: Optional[str] = None
    tipo: Optional[str] = None
    laboratorio_id: Optional[int] = None
    custodio_id: Optional[int] = None
    estado: str
    laboratorio: Optional[str] = None
    custodio: Optional[str] = None


class CatalogosResponse(BaseModel):
    laboratorios: List[Any]
    custodios: List[Any]
    tipos: List[str]
    estados: List[str]


class BienesListResponse(BaseModel):
    bienes: List[BienResponse]
    catalogos: CatalogosResponse


class BienDetailResponse(BaseModel):
    bien: BienResponse
