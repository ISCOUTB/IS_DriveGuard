"""
Rutas de sesiones (turnos de conduccion).
El conductor inicia y finaliza sus propias sesiones; supervisor y administrador
pueden asignar sesiones a cualquier conductor y consultarlas todas.
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.sesion import EstadoSesionEnum, Sesion
from app.models.usuario import Usuario
from app.schemas.sesion import SesionCreate, SesionFinalizar, SesionRead
from app.services import sesion_service

router = APIRouter(prefix="/sesiones", tags=["sesiones"])


@router.post("", response_model=SesionRead, status_code=status.HTTP_201_CREATED)
def iniciar_sesion(
    datos: SesionCreate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
) -> Sesion:
    """
    Inicia una sesion (conductor + vehiculo). Requiere conexion: el servidor fija
    fecha_hora_inicio. Un conductor solo puede iniciar sesiones propias.
    """
    return sesion_service.iniciar_sesion(db, datos, actual)


@router.get("", response_model=List[SesionRead])
def listar_sesiones(
    conductor_id: Optional[uuid.UUID] = None,
    vehiculo_id: Optional[uuid.UUID] = None,
    estado: Optional[EstadoSesionEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
) -> list:
    """Un conductor solo ve sus sesiones; supervisor y administrador ven todas."""
    return list(
        sesion_service.listar_sesiones(db, actual, conductor_id, vehiculo_id, estado, skip, limit)
    )


@router.get("/{sesion_id}", response_model=SesionRead)
def obtener_sesion(
    sesion_id: uuid.UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
) -> Sesion:
    return sesion_service.obtener_sesion(db, sesion_id, actual)


@router.post("/{sesion_id}/finalizar", response_model=SesionRead)
def finalizar_sesion(
    sesion_id: uuid.UUID,
    datos: Optional[SesionFinalizar] = Body(default=None),
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
) -> Sesion:
    """
    Cierra la sesion. El cuerpo es opcional: si el cliente cierra el turno estando
    offline puede enviar la fecha_hora_fin real; si no, se usa la hora del servidor.
    """
    fin = datos.fecha_hora_fin if datos else None
    return sesion_service.finalizar_sesion(db, sesion_id, actual, fin)