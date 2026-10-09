"""
Rutas de autenticacion: login de usuarios y consulta del perfil propio.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.usuario import UsuarioRead
from app.services.auth_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Valida credenciales y devuelve un JWT con el id y el rol del usuario."""
    usuario = authenticate_user(db, datos.correo, datos.password)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contrasena incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user_id=str(usuario.id), rol=usuario.rol.value)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UsuarioRead)
def me(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Perfil del usuario autenticado."""
    return usuario