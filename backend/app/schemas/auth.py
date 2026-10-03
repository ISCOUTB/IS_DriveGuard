
"""
Esquemas Pydantic de autenticacion (login y token JWT).
"""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Lo que el dashboard envia a POST /auth/login."""
    correo: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Lo que el backend devuelve tras un login exitoso."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    Forma de los datos codificados dentro del JWT (el 'sub' es el id del usuario).
    No viaja por la API directamente -- la usa app/api/deps.py al decodificar
    el token para resolver get_current_user().
    """
    sub: str
    rol: str
