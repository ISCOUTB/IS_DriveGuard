"""
Rutas de eventos de fatiga. Cubre RF9 (ingesta de eventos) y RF10/RF13/RF14
(consulta y filtrado de incidentes para el dashboard).
"""
import datetime
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.evento import Evento, SeveridadEnum
from app.models.usuario import RolEnum, Usuario
from app.schemas.evento import EventoCreate, EventoRead, EventoUpdate
from app.services import event_service
from app.services.event_service import ReferenciaNoEncontradaError

router = APIRouter(prefix="/events", tags=["events"])


def _obtener_o_404(db: Session, evento_id: uuid.UUID) -> Evento:
    evento = event_service.get_event(db, evento_id)
    if evento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    return evento


def _puede_ver(usuario: Usuario, evento: Evento) -> bool:
    """El conductor solo ve sus propios incidentes; admin/supervisor ven todo."""
    if usuario.rol in (RolEnum.ADMIN, RolEnum.SUPERVISOR):
        return True
    return evento.sesion.conductor_id == usuario.id


@router.post("", response_model=EventoRead, status_code=status.HTTP_201_CREATED)
def crear_evento(
    datos: EventoCreate,
    response: Response,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> Evento:
    """Ingesta de eventos desde el modulo de CV.

    Idempotente por ``id`` (generado en el cliente): si el evento ya existe
    se devuelve el original con 200 en lugar de duplicarlo.
    """
    try:
        evento, creado = event_service.create_event(db, datos)
    except ReferenciaNoEncontradaError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    if not creado:
        response.status_code = status.HTTP_200_OK
    return evento


@router.get("", response_model=List[EventoRead])
def listar_eventos(
    driver_id: Optional[uuid.UUID] = Query(default=None, alias="driver"),
    sesion_id: Optional[uuid.UUID] = None,
    tipo: Optional[uuid.UUID] = Query(default=None, alias="type"),
    severidad: Optional[SeveridadEnum] = None,
    revisado: Optional[bool] = None,
    fecha_desde: Optional[datetime.datetime] = Query(default=None, alias="date_from"),
    fecha_hasta: Optional[datetime.datetime] = Query(default=None, alias="date_to"),
    fecha: Optional[datetime.date] = Query(
        default=None,
        description="Atajo: filtra por dia calendario (equivale a date_from/date_to).",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
) -> list:
    """Consulta filtrada para el dashboard (RF10/RF13/RF14).

    Acepta ``?driver=&type=&date_from=&date_to=`` (mas ``severidad``,
    ``revisado``, ``sesion_id`` y el atajo ``date`` por dia). El conductor
    solo puede consultar sus propios incidentes: cualquier ``driver`` distinto
    a su id se ignora y se fuerza a su propio id.
    """
    if fecha is not None and (fecha_desde is None and fecha_hasta is None):
        fecha_desde = datetime.datetime.combine(fecha, datetime.time.min)
        fecha_hasta = datetime.datetime.combine(fecha, datetime.time.max)

    if actual.rol == RolEnum.DRIVER:
        # El conductor solo ve lo suyo, aunque pida otro driver_id.
        driver_id = actual.id

    return list(
        event_service.get_filtered_events(
            db,
            driver_id=driver_id,
            sesion_id=sesion_id,
            tipo_incidente_id=tipo,
            severidad=severidad,
            revisado=revisado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            skip=skip,
            limit=limit,
        )
    )


@router.get("/{evento_id}", response_model=EventoRead)
def obtener_evento(
    evento_id: uuid.UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
) -> Evento:
    """Detalle de un evento, con control de acceso por rol."""
    evento = _obtener_o_404(db, evento_id)
    if not _puede_ver(actual, evento):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Sin permisos sobre este evento"
        )
    return evento


@router.patch("/{evento_id}", response_model=EventoRead)
def actualizar_evento(
    evento_id: uuid.UUID,
    datos: EventoUpdate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
) -> Evento:
    """Marca revision / agrega comentario del conductor.

    El conductor solo puede comentar sus propios eventos; marcar ``revisado``
    queda reservado a supervisor y administrador.
    """
    evento = _obtener_o_404(db, evento_id)
    if not _puede_ver(actual, evento):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Sin permisos sobre este evento"
        )
    cambios = datos.model_dump(exclude_unset=True)
    if "revisado" in cambios and actual.rol == RolEnum.DRIVER:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Solo un supervisor o administrador puede marcar revision",
        )
    return event_service.update_event(db, evento, datos)
