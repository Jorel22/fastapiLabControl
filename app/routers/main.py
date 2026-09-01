"""Router principal: verificación de estado y health check."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["General"])


@router.get("/")
def index():
    """Página de inicio de la API."""
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "app": "LabControl Mecánica ESPOCH API", "version": "1.0.0"}
    )


@router.get("/health")
def health():
    """Verificación de estado de la app."""
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "app": "LabControl Mecánica ESPOCH API"}
    )
