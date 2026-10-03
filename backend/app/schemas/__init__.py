# schemas/__init__.py
from schemas.auth import LoginRequest, TokenPayload, TokenResponse
from schemas.evento import EventoBase, EventoCreate, EventoRead, EventoUpdate
from schemas.sesion import SesionBase, SesionCreate, SesionRead, SesionUpdate
from schemas.tipo_incidente import (
    TipoIncidenteBase,
    TipoIncidenteCreate,
    TipoIncidenteRead,
    TipoIncidenteUpdate,
)
from schemas.usuario import UsuarioBase, UsuarioCreate, UsuarioRead, UsuarioUpdate
from schemas.vehiculo import VehiculoBase, VehiculoCreate, VehiculoRead, VehiculoUpdate

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