"""Configuración de la aplicación LabControl Mecánica ESPOCH (FastAPI).

Define las clases y variables de configuración para los distintos entornos.
"""
import os
from datetime import timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _normalize_db_url(url: Optional[str], default: str) -> str:
    if not url:
        return default
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Settings:
    """Configuración base común a todos los entornos."""
    PROJECT_NAME: str = "LabControl Mecánica ESPOCH API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API REST de control de inventario y mantenimientos de laboratorios - ESPOCH"
    
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion-de-32-bytes-minimo")
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "cambia-esta-clave-jwt-super-secreta-32-bytes")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES: int = 30
    JWT_ACCESS_COOKIE_NAME: str = "access_token_cookie"
    
    DATABASE_URL: str = _normalize_db_url(
        os.environ.get("DATABASE_URL"),
        f"sqlite:///{os.path.join(BASE_DIR, 'labcontrol.db')}"
    )
    DEBUG: bool = True
    TESTING: bool = False


class DevelopmentSettings(Settings):
    DEBUG: bool = True
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'labcontrol.db')}"
    )


class TestingSettings(Settings):
    DEBUG: bool = True
    TESTING: bool = True
    DATABASE_URL: str = "sqlite:///:memory:"


class ProductionSettings(Settings):
    DEBUG: bool = False
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///labcontrol.db")


settings_by_name = {
    "development": DevelopmentSettings,
    "testing": TestingSettings,
    "production": ProductionSettings,
    "default": DevelopmentSettings,
}


def get_settings(env: Optional[str] = None) -> Settings:
    config_name = env or os.environ.get("FASTAPI_CONFIG") or os.environ.get("FLASK_CONFIG") or "development"
    settings_cls = settings_by_name.get(config_name, settings_by_name["default"])
    return settings_cls()


settings = get_settings()
