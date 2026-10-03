# schemas/__init__.py
from app.schemas.auth import LoginRequest, TokenPayload, TokenResponse
from app.schemas.evento import EventoBase, EventoCreate, EventoRead, EventoUpdate
from app.schemas.sesion import SesionBase, SesionCreate, SesionRead, SesionUpdate
from app.schemas.tipo_incidente import (
    TipoIncidenteBase,
    TipoIncidenteCreate,
    TipoIncidenteRead,
    TipoIncidenteUpdate,
)
from app.schemas.usuario import UsuarioBase, UsuarioCreate, UsuarioRead, UsuarioUpdate
from app.schemas.vehiculo import VehiculoBase, VehiculoCreate, VehiculoRead, VehiculoUpdate

__all__ = [
    "LoginRequest",
    "TokenPayload",
    "TokenResponse",
    "EventoBase",
    "EventoCreate",
    "EventoRead",
    "EventoUpdate",
    "SesionBase",
    "SesionCreate",
    "SesionRead",
    "SesionUpdate",
    "TipoIncidenteBase",
    "TipoIncidenteCreate",
    "TipoIncidenteRead",
    "TipoIncidenteUpdate",
    "UsuarioBase",
    "UsuarioCreate",
    "UsuarioRead",
    "UsuarioUpdate",
    "VehiculoBase",
    "VehiculoCreate",
    "VehiculoRead",
    "VehiculoUpdate",
]