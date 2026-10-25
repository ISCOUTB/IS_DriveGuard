"""
Rutas del catalogo de tipos de incidente y sus umbrales de sensibilidad.
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.tipo_incidente import TipoIncidente
from app.models.usuario import RolEnum, Usuario
from app.schemas.tipo_incidente import (
    TipoIncidenteCreate,
    TipoIncidenteRead,
    TipoIncidenteUpdate,
)
from app.services import tipo_incidente_service

router = APIRouter(prefix="/tipos-incidentes", tags=["tipos-incidentes"])


@router.get("", response_model=List[TipoIncidenteRead])
def listar_tipos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list:
    """Catalogo completo. El cliente de captura lo consulta para obtener los umbrales vigentes."""
    return list(tipo_incidente_service.listar_tipos(db))


@router.get("/{tipo_id}", response_model=TipoIncidenteRead)
def obtener_tipo(
    tipo_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> TipoIncidente:
    return tipo_incidente_service.obtener_tipo(db, tipo_id)


@router.post("", response_model=TipoIncidenteRead, status_code=status.HTTP_201_CREATED)
def crear_tipo(
    datos: TipoIncidenteCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(RolEnum.ADMIN)),
) -> TipoIncidente:
    """Solo administrador."""
    return tipo_incidente_service.crear_tipo(db, datos)


@router.patch("/{tipo_id}", response_model=TipoIncidenteRead)
def actualizar_tipo(
    tipo_id: uuid.UUID,
    datos: TipoIncidenteUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(RolEnum.ADMIN)),
) -> TipoIncidente:
    """Ajusta umbrales y descripcion. Solo administrador."""
    return tipo_incidente_service.actualizar_tipo(db, tipo_id, datos)