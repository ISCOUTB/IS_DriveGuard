"""
Rutas de gestion de vehiculos. No hay DELETE: la baja se hace con estado = inactivo.
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.usuario import RolEnum, Usuario
from app.models.vehiculo import EstadoVehiculoEnum, TipoVehiculoEnum, Vehiculo
from app.schemas.vehiculo import VehiculoCreate, VehiculoRead, VehiculoUpdate
from app.services import vehiculo_service

router = APIRouter(prefix="/vehiculos", tags=["vehiculos"])

_GESTORES = (RolEnum.ADMIN, RolEnum.SUPERVISOR)


@router.post("", response_model=VehiculoRead, status_code=status.HTTP_201_CREATED)
def crear_vehiculo(
    datos: VehiculoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(*_GESTORES)),
) -> Vehiculo:
    """Registra un vehiculo. Administrador o supervisor."""
    return vehiculo_service.crear_vehiculo(db, datos)


@router.get("", response_model=List[VehiculoRead])
def listar_vehiculos(
    estado: Optional[EstadoVehiculoEnum] = None,
    tipo_vehiculo: Optional[TipoVehiculoEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list:
    """Lista vehiculos. Cualquier usuario autenticado (el conductor elige uno al iniciar sesion)."""
    return list(vehiculo_service.listar_vehiculos(db, estado, tipo_vehiculo, skip, limit))


@router.get("/{vehiculo_id}", response_model=VehiculoRead)
def obtener_vehiculo(
    vehiculo_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> Vehiculo:
    return vehiculo_service.obtener_vehiculo(db, vehiculo_id)


@router.patch("/{vehiculo_id}", response_model=VehiculoRead)
def actualizar_vehiculo(
    vehiculo_id: uuid.UUID,
    datos: VehiculoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(*_GESTORES)),
) -> Vehiculo:
    """Edita datos o cambia el estado (activo, mantenimiento, inactivo). Administrador o supervisor."""
    return vehiculo_service.actualizar_vehiculo(db, vehiculo_id, datos)