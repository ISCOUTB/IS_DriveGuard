"""
Dependencias reutilizables entre routers: sesion de BD, usuario autenticado
y control de acceso por rol.
"""
import uuid
from typing import Callable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.usuario import RolEnum, Usuario

# auto_error=False para responder nosotros 401 (HTTPBearer responde 403 por defecto
# cuando falta el header).
bearer_scheme = HTTPBearer(auto_error=False)

__all__ = ["get_db", "get_current_user", "require_roles"]


def _credenciales_invalidas() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas o sesion expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Resuelve el usuario a partir del JWT del header Authorization, o lanza 401."""
    if credentials is None:
        raise _credenciales_invalidas()

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise _credenciales_invalidas()

    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError:
        raise _credenciales_invalidas()

    usuario = db.get(Usuario, user_id)
    if usuario is None or not usuario.activo:
        raise _credenciales_invalidas()
    return usuario


def require_roles(*roles: RolEnum) -> Callable[..., Usuario]:
    """
    Fabrica de dependencias: permite el acceso solo a los roles indicados.
    Uso: Depends(require_roles(RolEnum.SUPERVISOR, RolEnum.ADMIN))
    """

    def _verificar(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta accion",
            )
        return usuario

    return _verificar