"""Esquemas Pydantic para validación y serialización en FastAPI."""
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    PerfilResponse,
    MessageResponse,
)
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioResetPassword,
    UsuarioResponse,
    UsuariosListResponse,
)
from app.schemas.bien import (
    BienCreate,
    BienUpdate,
    BienResponse,
    BienesListResponse,
    BienDetailResponse,
)
from app.schemas.mantenimiento import (
    MantenimientoCreate,
    MantenimientoResponse,
    HistoricoResponse,
)
from app.schemas.software import (
    SoftwareCreate,
    SoftwareResponse,
    BienSoftwareListResponse,
)
from app.schemas.reporte import (
    ReporteResponse,
)

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "PerfilResponse",
    "MessageResponse",
    "UsuarioCreate",
    "UsuarioResetPassword",
    "UsuarioResponse",
    "UsuariosListResponse",
    "BienCreate",
    "BienUpdate",
    "BienResponse",
    "BienesListResponse",
    "BienDetailResponse",
    "MantenimientoCreate",
    "MantenimientoResponse",
    "HistoricoResponse",
    "SoftwareCreate",
    "SoftwareResponse",
    "BienSoftwareListResponse",
    "ReporteResponse",
]
