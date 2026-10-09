"""
Logica de negocio de autenticacion: verificar credenciales y emitir el token.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.usuario import Usuario

# Hash de relleno para igualar el tiempo de respuesta cuando el correo no existe
# (evita que un atacante distinga "correo inexistente" de "contrasena incorrecta"
# midiendo cuanto tarda la respuesta).
_DUMMY_HASH = hash_password("contrasena-de-relleno")


def authenticate_user(db: Session, correo: str, password: str) -> Optional[Usuario]:
    """
    Devuelve el usuario si las credenciales son validas y esta activo.
    Devuelve None en cualquier otro caso, sin revelar el motivo.
    """
    usuario = db.scalar(select(Usuario).where(Usuario.correo == correo))
    if usuario is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, usuario.contrasena_hash):
        return None
    if not usuario.activo:
        return None
    return usuario