"""
Rutas de eventos de fatiga: ingesta idempotente desde el cliente de captura y
consulta/filtrado para el dashboard.
"""
import datetime
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.evento import Evento, SeveridadEnum
from app.models.usuario import RolEnum, Usuario
from app.schemas.evento import (
    EventoCreate,
    EventoLoteCreate,
    EventoLoteResultado,
    EventoRead,
    EventoUpdate,
    ResumenEventos,
)
from app.services import evento_service

router = APIRouter(prefix="/eventos", tags=["eventos"])

# Quien puede enviar eventos: el cliente de captura (autenticado como conductor) y el administrador.
_EMISORES = (RolEnum.DRIVER, RolEnum.ADMIN)


@router.post(
    "",
    response_model=EventoRead,
    status_code=status.HTTP_201_CREATED,
    responses={200: {"description": "El evento ya habia sido recibido (reintento idempotente)"}},
)
def registrar_evento(
    datos: EventoCreate,
    response: Response,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_roles(*_EMISORES)),
) -> Evento:
    """
    Registra un evento. El id lo genera el cliente: si lo reenvia, el servidor responde 200
    con el evento ya guardado en lugar de duplicarlo.
    """
    evento, creado = evento_service.registrar_evento(db, datos, actual)
    if not creado:
        response.status_code = status.HTTP_200_OK
    return evento


@router.post("/lote", response_model=EventoLoteResultado)
def registrar_lote(
    datos: EventoLoteCreate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_roles(*_EMISORES)),
) -> dict:
    """Vacia la cola offline: hasta 500 eventos en una sola transaccion (todo o nada)."""
    return evento_service.registrar_lote(db, datos.eventos, actual)


@router.get("/resumen", response_model=ResumenEventos)
def resumen_eventos(
    conductor_id: Optional[uuid.UUID] = None,
    vehiculo_id: Optional[uuid.UUID] = None,
    tipo_incidente_id: Optional[uuid.UUID] = None,
    severidad: Optional[SeveridadEnum] = None,
    desde: Optional[datetime.datetime] = None,
    hasta: Optional[datetime.datetime] = None,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
) -> dict:
    """Agregaciones para el dashboard. Un conductor solo ve las suyas."""
    return evento_service.resumen_eventos(
        db,
        actual,
        conductor_id=conductor_id,
        vehiculo_id=vehiculo_id,
        tipo_incidente_id=tipo_incidente_id,
        severidad=severidad,
        desde=desde,
        hasta=hasta,
    )


@router.get("", response_model=List[EventoRead])
def listar_eventos(
    conductor_id: Optional[uuid.UUID] = None,
    vehiculo_id: Optional[uuid.UUID] = None,
    sesion_id: Optional[uuid.UUID] = None,
    tipo_incidente_id: Optional[uuid.UUID] = None,
    severidad: Optional[SeveridadEnum] = None,
    revisado: Optional[bool] = None,
    desde: Optional[datetime.datetime] = None,
    hasta: Optional[datetime.datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
) -> list:
    """Eventos filtrados, del mas reciente al mas antiguo. Un conductor solo ve los suyos."""
    return list(
        evento_service.listar_eventos(
            db,
            actual,
            skip=skip,
            limit=limit,
            conductor_id=conductor_id,
            vehiculo_id=vehiculo_id,
            sesion_id=sesion_id,
            tipo_incidente_id=tipo_incidente_id,
            severidad=severidad,
            revisado=revisado,
            desde=desde,
            hasta=hasta,
        )
    )


@router.get("/{evento_id}", response_model=EventoRead)
def obtener_evento(
    evento_id: uuid.UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
) -> Evento:
    return evento_service.obtener_evento(db, evento_id, actual)


@router.patch("/{evento_id}", response_model=EventoRead)
def actualizar_evento(
    evento_id: uuid.UUID,
    datos: EventoUpdate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
) -> Evento:
    """El conductor comenta sus eventos; el supervisor los marca como revisados; el administrador ambos."""
    return evento_service.actualizar_evento(db, evento_id, datos, actual)