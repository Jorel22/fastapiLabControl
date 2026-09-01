"""Application factory de LabControl Mecánica ESPOCH (FastAPI).

Crea y configura la instancia de FastAPI, middleware de CORS,
cabeceras de seguridad HTTP, manejadores de excepciones y routers.
"""
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from app.core.database import Base, engine
from app.routers import (
    auth_router,
    bienes_router,
    main_router,
    mantenimientos_router,
    reportes_router,
    usuarios_router,
)


def create_app(env: Optional[str] = None) -> FastAPI:
    """Construye la aplicación FastAPI con la configuración indicada."""
    settings = get_settings(env)

    # Crear tablas si no existen (en desarrollo / testing)
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware de Cabeceras de Seguridad HTTP
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permitir recursos de Swagger UI (cdn.jsdelivr.net) y fuentes para /docs y /redoc
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "connect-src 'self' *;"
        )
        return response

    # Manejadores de excepciones personalizados
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc: HTTPException):
        content = exc.detail if isinstance(exc.detail, dict) else {"error": exc.detail}
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Simplifica el mensaje de error de validación para mantener consistencia
        errors = exc.errors()
        msg = errors[0].get("msg", "Error de validación de datos.") if errors else "Error de validación."
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": msg, "detalles": exc.errors()},
        )

    # Registro de routers
    app.include_router(main_router)
    app.include_router(auth_router)
    app.include_router(bienes_router)
    app.include_router(mantenimientos_router)
    app.include_router(reportes_router)
    app.include_router(usuarios_router)

    return app


app = create_app()
