"""
Utilidades de seguridad: hashing de contrasenas (bcrypt) y tokens JWT.
Usadas por app/services/auth_service.py y app/api/deps.py.
"""
import datetime
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.schemas.auth import TokenPayload

ALGORITHM = "HS256"
BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    """Devuelve el hash bcrypt de la contrasena (incluye la sal)."""
    secret = password.encode("utf-8")
    if len(secret) > BCRYPT_MAX_BYTES:
        raise ValueError("La contrasena no puede superar 72 bytes")
    return bcrypt.hashpw(secret, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """True si la contrasena coincide con el hash guardado."""
    secret = password.encode("utf-8")
    if len(secret) > BCRYPT_MAX_BYTES:
        return False
    return bcrypt.checkpw(secret, password_hash.encode("utf-8"))


def create_access_token(user_id: str, rol: str) -> str:
    """Genera un JWT firmado con 'sub' (id de usuario), 'rol' y expiracion."""
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": user_id, "rol": rol, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[TokenPayload]:
    """Devuelve el payload validado, o None si el token es invalido o expiro."""
    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(sub=data["sub"], rol=data["rol"])
    except (JWTError, KeyError, ValueError):
        return None