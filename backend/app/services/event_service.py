"""
Logica de negocio de eventos: clasificacion de severidad y agregaciones para
el dashboard (incidentes por conductor, por semana, etc.).
"""
import datetime
import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.evento import Evento, SeveridadEnum
from app.models.sesion import Sesion
from app.models.tipo_incidente import TipoIncidente
from app.schemas.evento import EventoCreate, EventoUpdate


class ReferenciaNoEncontradaError(Exception):
    """La sesion o el tipo de incidente no existen. La ruta lo traduce a 404."""


def create_event(db: Session, datos: EventoCreate) -> tuple[Evento, bool]:
    """Inserta un evento con el id generado por el cliente.

    Idempotente (RNF-02): si el id ya existe se devuelve el evento original
    con ``creado=False`` en lugar de duplicarlo, para que el cliente pueda
    reintentar el envio tras recuperar conexion sin perder ni duplicar.
    Devuelve ``(evento, creado)``.
    """
    existente = db.get(Evento, datos.id)
    if existente is not None:
        return existente, False

    if db.get(Sesion, datos.sesion_id) is None:
        raise ReferenciaNoEncontradaError("La sesion indicada no existe")
    if db.get(TipoIncidente, datos.tipo_incidente_id) is None:
        raise ReferenciaNoEncontradaError("El tipo de incidente indicado no existe")

    evento = Evento(
        id=datos.id,
        sesion_id=datos.sesion_id,
        tipo_incidente_id=datos.tipo_incidente_id,
        fecha_hora=datos.fecha_hora,
        duracion_segundos=datos.duracion_segundos,
        severidad=datos.severidad,
        valor_metrica=datos.valor_metrica,
        comentario_conductor=datos.comentario_conductor,
    )
    db.add(evento)
    try:
        db.commit()
    except IntegrityError:
        # Carrera: otro request inserto el mismo id entre el SELECT y el INSERT.
        db.rollback()
        existente = db.get(Evento, datos.id)
        if existente is not None:
            return existente, False
        raise
    db.refresh(evento)
    return evento, True


def get_event(db: Session, evento_id: uuid.UUID) -> Optional[Evento]:
    return db.get(Evento, evento_id)


def get_filtered_events(
    db: Session,
    driver_id: Optional[uuid.UUID] = None,
    sesion_id: Optional[uuid.UUID] = None,
    tipo_incidente_id: Optional[uuid.UUID] = None,
    severidad: Optional[SeveridadEnum] = None,
    revisado: Optional[bool] = None,
    fecha_desde: Optional[datetime.datetime] = None,
    fecha_hasta: Optional[datetime.datetime] = None,
    skip: int = 0,
    limit: int = 50,
) -> Sequence[Evento]:
    """Consulta filtrada para el dashboard (RF10/RF13/RF14)."""
    consulta = select(Evento).order_by(Evento.fecha_hora.desc())
    if driver_id is not None or sesion_id is not None:
        consulta = consulta.join(Sesion, Sesion.id == Evento.sesion_id)
    if driver_id is not None:
        consulta = consulta.where(Sesion.conductor_id == driver_id)
    if sesion_id is not None:
        consulta = consulta.where(Evento.sesion_id == sesion_id)
    if tipo_incidente_id is not None:
        consulta = consulta.where(Evento.tipo_incidente_id == tipo_incidente_id)
    if severidad is not None:
        consulta = consulta.where(Evento.severidad == severidad)
    if revisado is not None:
        consulta = consulta.where(Evento.revisado == revisado)
    if fecha_desde is not None:
        consulta = consulta.where(Evento.fecha_hora >= fecha_desde)
    if fecha_hasta is not None:
        consulta = consulta.where(Evento.fecha_hora <= fecha_hasta)
    return db.scalars(consulta.offset(skip).limit(limit)).all()


def update_event(db: Session, evento: Evento, datos: EventoUpdate) -> Evento:
    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(evento, campo, valor)
    db.commit()
    db.refresh(evento)
    return evento
