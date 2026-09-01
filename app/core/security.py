"""Módulo de seguridad, hashing de contraseñas y autenticación JWT."""
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from config import settings
from app.core.database import get_db


def hash_password(password: str) -> str:
    """Genera el hash seguro de la contraseña usando bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña plana coincide con el hash."""
    if not hashed_password or not plain_password:
        return False
    try:
        # Si es un hash bcrypt estándar
        if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        # Compatibilidad con hashes de Werkzeug pbkdf2/scrypt si se reutiliza base de datos
        from werkzeug.security import check_password_hash
        return check_password_hash(hashed_password, plain_password)
    except Exception:
        return False


def create_access_token(identity: str, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT firmado con la identidad (ID del usuario)."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRES_MINUTES)
    
    to_encode = {
        "sub": str(identity),
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "nbf": int(datetime.now(timezone.utc).timestamp()),
        "type": "access",
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica y valida un token JWT."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extrae el token JWT desde las cookies o desde el header Authorization."""
    # 1. Intentar desde cookie HttpOnly
    token = request.cookies.get(settings.JWT_ACCESS_COOKIE_NAME)
    if token:
        return token
    
    # 2. Intentar desde header Authorization: Bearer <token>
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
        
    return None


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
):
    """Obtiene el usuario autenticado si existe un token válido en la petición."""
    token = extract_token_from_request(request)
    if not token:
        return None
    
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    
    user_id = payload.get("sub")
    try:
        from app.models.usuario import Usuario
        user = db.get(Usuario, int(user_id))
        return user
    except (ValueError, TypeError):
        return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """Dependencia de FastAPI que asegura que la petición cuente con un usuario autenticado válido y activo."""
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Falta el token de autenticación."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Token inválido o expirado."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    try:
        from app.models.usuario import Usuario
        user = db.get(Usuario, int(user_id))
    except (ValueError, TypeError):
        user = None

    if user is None or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Usuario no encontrado o inactivo."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_admin(
    current_user=Depends(get_current_user)
):
    """Dependencia de FastAPI que restringe el acceso únicamente a usuarios con perfil 'administrador'."""
    if not current_user.es_administrador:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Acceso restringido a administradores."},
        )
    return current_user
