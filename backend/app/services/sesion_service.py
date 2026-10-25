"""
Logica de negocio de sesiones (turnos de conduccion).
Aqui vive la regla que el esquema no puede garantizar: Sesion.conductor_id debe
apuntar a un usuario con rol conductor.
"""
import datetime
import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tiempo import a_utc_naive, ahora_utc
from app.models.sesion import EstadoSesionEnum, Sesion
from app.models.usuario import RolEnum, Usuario
from app.models.vehiculo import EstadoVehiculoEnum, Vehiculo
from app.schemas.sesion import SesionCreate
from app.services.errors import ConflictoError, NoEncontradoError, PermisoError, ReglaNegocioError


def iniciar_sesion(db: Session, datos: SesionCreate, actual: Usuario) -> Sesion:
    if actual.rol == RolEnum.DRIVER and datos.conductor_id != actual.id:
        raise PermisoError("Un conductor solo puede iniciar sesiones propias")

    conductor = db.get(Usuario, datos.conductor_id)
    if conductor is None:
        raise NoEncontradoError("Conductor no encontrado")
    if conductor.rol != RolEnum.DRIVER:
        raise ReglaNegocioError("El usuario indicado no tiene rol conductor")
    if not conductor.activo:
        raise ReglaNegocioError("El conductor esta desactivado")

    vehiculo = db.get(Vehiculo, datos.vehiculo_id)
    if vehiculo is None:
        raise NoEncontradoError("Vehiculo no encontrado")
    if vehiculo.estado != EstadoVehiculoEnum.ACTIVO:
        raise ReglaNegocioError("El vehiculo no esta disponible (estado distinto de activo)")

    if db.scalar(
        select(Sesion.id).where(
            Sesion.conductor_id == conductor.id, Sesion.estado == EstadoSesionEnum.ACTIVA
        )
    ):
        raise ConflictoError("El conductor ya tiene una sesion activa")
    if db.scalar(
        select(Sesion.id).where(
            Sesion.vehiculo_id == vehiculo.id, Sesion.estado == EstadoSesionEnum.ACTIVA
        )
    ):
        raise ConflictoError("El vehiculo ya tiene una sesion activa")

    sesion = Sesion(
        conductor_id=conductor.id,
        vehiculo_id=vehiculo.id,
        fecha_hora_inicio=ahora_utc(),
        estado=EstadoSesionEnum.ACTIVA,
    )
    db.add(sesion)
    db.commit()
    db.refresh(sesion)
    return sesion


def obtener_sesion(db: Session, sesion_id: uuid.UUID, actual: Usuario) -> Sesion:
    sesion = db.get(Sesion, sesion_id)
    if sesion is None:
        raise NoEncontradoError("Sesion no encontrada")
    if actual.rol == RolEnum.DRIVER and sesion.conductor_id != actual.id:
        raise PermisoError("Sin permisos sobre esta sesion")
    return sesion


def listar_sesiones(
    db: Session,
    actual: Usuario,
    conductor_id: Optional[uuid.UUID] = None,
    vehiculo_id: Optional[uuid.UUID] = None,
    estado: Optional[EstadoSesionEnum] = None,
    skip: int = 0,
    limit: int = 50,
) -> Sequence[Sesion]:
    if actual.rol == RolEnum.DRIVER:
        if conductor_id not in (None, actual.id):
            raise PermisoError("Un conductor solo puede consultar sus propias sesiones")
        conductor_id = actual.id

    consulta = select(Sesion).order_by(Sesion.fecha_hora_inicio.desc())
    if conductor_id is not None:
        consulta = consulta.where(Sesion.conductor_id == conductor_id)
    if vehiculo_id is not None:
        consulta = consulta.where(Sesion.vehiculo_id == vehiculo_id)
    if estado is not None:
        consulta = consulta.where(Sesion.estado == estado)
    return db.scalars(consulta.offset(skip).limit(limit)).all()


def finalizar_sesion(
    db: Session,
    sesion_id: uuid.UUID,
    actual: Usuario,
    fecha_hora_fin: Optional[datetime.datetime] = None,
) -> Sesion:
    sesion = obtener_sesion(db, sesion_id, actual)
    if sesion.estado == EstadoSesionEnum.FINALIZADA:
        raise ConflictoError("La sesion ya esta finalizada")

    fin = a_utc_naive(fecha_hora_fin) or ahora_utc()
    if fin < sesion.fecha_hora_inicio:
        raise ReglaNegocioError("fecha_hora_fin no puede ser anterior al inicio de la sesion")

    sesion.fecha_hora_fin = fin
    sesion.estado = EstadoSesionEnum.FINALIZADA
    db.commit()
    db.refresh(sesion)
    return sesion