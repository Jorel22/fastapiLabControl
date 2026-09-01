"""Módulo de routers de la API."""
from app.routers.auth import router as auth_router
from app.routers.bienes import router as bienes_router
from app.routers.main import router as main_router
from app.routers.mantenimientos import router as mantenimientos_router
from app.routers.reportes import router as reportes_router
from app.routers.usuarios import router as usuarios_router

__all__ = [
    "auth_router",
    "bienes_router",
    "main_router",
    "mantenimientos_router",
    "reportes_router",
    "usuarios_router",
]
