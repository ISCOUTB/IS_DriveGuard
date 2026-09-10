"""
Rutas de autenticacion. Cubre RF12 (login de supervisores).
"""
from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

# TODO: implementar POST /auth/login siguiendo el diagrama de secuencia de
# autenticacion del supervisor.
