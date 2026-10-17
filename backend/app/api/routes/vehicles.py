"""
Rutas de gestion de vehiculos. Cubre RF11 (CRUD de conductores y vehiculos).
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.usuario import RolEnum
from app.models.vehiculo import Vehiculo
from app.schemas.vehiculo import VehiculoCreate, VehiculoRead, VehiculoUpdate
from app.services import vehiculo_service
from app.services.vehiculo_service import ConflictoError, ReglaNegocioError

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def _obtener_o_404(db: Session, vehiculo_id: uuid.UUID) -> Vehiculo:
    vehiculo = vehiculo_service.obtener_vehiculo(db, vehiculo_id)
    if vehiculo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Vehiculo no encontrado")
    return vehiculo


@router.post("", response_model=VehiculoRead, status_code=status.HTTP_201_CREATED)
def crear_vehiculo(
    datos: VehiculoCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(RolEnum.ADMIN)),
) -> Vehiculo:
    """Registra un vehiculo en la flota. Solo administrador."""
    try:
        return vehiculo_service.crear_vehiculo(db, datos)
    except ConflictoError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=List[VehiculoRead])
def listar_vehiculos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(RolEnum.ADMIN, RolEnum.SUPERVISOR)),
) -> list:
    """Lista la flota. Solo administrador y supervisor."""
    return list(vehiculo_service.listar_vehiculos(db, skip, limit))


@router.get("/{vehiculo_id}", response_model=VehiculoRead)
def obtener_vehiculo(
    vehiculo_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(RolEnum.ADMIN, RolEnum.SUPERVISOR)),
) -> Vehiculo:
    """Detalle de un vehiculo. Solo administrador y supervisor."""
    return _obtener_o_404(db, vehiculo_id)


@router.patch("/{vehiculo_id}", response_model=VehiculoRead)
def actualizar_vehiculo(
    vehiculo_id: uuid.UUID,
    datos: VehiculoUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(RolEnum.ADMIN)),
) -> Vehiculo:
    """Actualiza un vehiculo. Solo administrador."""
    vehiculo = _obtener_o_404(db, vehiculo_id)
    try:
        return vehiculo_service.actualizar_vehiculo(db, vehiculo, datos)
    except ConflictoError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{vehiculo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_vehiculo(
    vehiculo_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(RolEnum.ADMIN)),
) -> None:
    """Elimina un vehiculo sin historial. Solo administrador."""
    vehiculo = _obtener_o_404(db, vehiculo_id)
    try:
        vehiculo_service.eliminar_vehiculo(db, vehiculo)
    except ReglaNegocioError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))
    return None
