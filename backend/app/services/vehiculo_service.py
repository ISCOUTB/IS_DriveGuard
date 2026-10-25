"""
Logica de negocio de vehiculos. No hay borrado: la baja es estado = inactivo.
"""
import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.sesion import EstadoSesionEnum, Sesion
from app.models.vehiculo import EstadoVehiculoEnum, TipoVehiculoEnum, Vehiculo
from app.schemas.vehiculo import VehiculoCreate, VehiculoUpdate
from app.services.errors import ConflictoError, NoEncontradoError, ReglaNegocioError


def _normalizar_placa(placa: str) -> str:
    return placa.strip().upper()


def _placa_en_uso(db: Session, placa: str, excluir_id: Optional[uuid.UUID] = None) -> bool:
    consulta = select(Vehiculo.id).where(Vehiculo.placa == placa)
    if excluir_id is not None:
        consulta = consulta.where(Vehiculo.id != excluir_id)
    return db.scalar(consulta) is not None


def crear_vehiculo(db: Session, datos: VehiculoCreate) -> Vehiculo:
    placa = _normalizar_placa(datos.placa)
    if not placa:
        raise ReglaNegocioError("La placa no puede estar vacia")
    if _placa_en_uso(db, placa):
        raise ConflictoError("Ya existe un vehiculo con esa placa")
    vehiculo = Vehiculo(
        placa=placa,
        tipo_vehiculo=datos.tipo_vehiculo,
        marca=datos.marca,
        modelo=datos.modelo,
        estado=EstadoVehiculoEnum.ACTIVO,
    )
    db.add(vehiculo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictoError("Ya existe un vehiculo con esa placa")
    db.refresh(vehiculo)
    return vehiculo


def obtener_vehiculo(db: Session, vehiculo_id: uuid.UUID) -> Vehiculo:
    vehiculo = db.get(Vehiculo, vehiculo_id)
    if vehiculo is None:
        raise NoEncontradoError("Vehiculo no encontrado")
    return vehiculo


def listar_vehiculos(
    db: Session,
    estado: Optional[EstadoVehiculoEnum] = None,
    tipo_vehiculo: Optional[TipoVehiculoEnum] = None,
    skip: int = 0,
    limit: int = 50,
) -> Sequence[Vehiculo]:
    consulta = select(Vehiculo).order_by(Vehiculo.placa)
    if estado is not None:
        consulta = consulta.where(Vehiculo.estado == estado)
    if tipo_vehiculo is not None:
        consulta = consulta.where(Vehiculo.tipo_vehiculo == tipo_vehiculo)
    return db.scalars(consulta.offset(skip).limit(limit)).all()


def actualizar_vehiculo(db: Session, vehiculo_id: uuid.UUID, datos: VehiculoUpdate) -> Vehiculo:
    vehiculo = obtener_vehiculo(db, vehiculo_id)
    cambios = datos.model_dump(exclude_unset=True)

    for campo in ("placa", "tipo_vehiculo", "estado"):
        if campo in cambios and cambios[campo] is None:
            raise ReglaNegocioError(f"{campo} no puede ser nulo")

    if "placa" in cambios:
        cambios["placa"] = _normalizar_placa(cambios["placa"])
        if not cambios["placa"]:
            raise ReglaNegocioError("La placa no puede estar vacia")
        if _placa_en_uso(db, cambios["placa"], excluir_id=vehiculo.id):
            raise ConflictoError("Ya existe un vehiculo con esa placa")

    nuevo_estado = cambios.get("estado")
    if nuevo_estado is not None and nuevo_estado != EstadoVehiculoEnum.ACTIVO:
        en_uso = db.scalar(
            select(Sesion.id).where(
                Sesion.vehiculo_id == vehiculo.id,
                Sesion.estado == EstadoSesionEnum.ACTIVA,
            )
        )
        if en_uso:
            raise ConflictoError("El vehiculo tiene una sesion activa; finalizala primero")

    for campo, valor in cambios.items():
        setattr(vehiculo, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictoError("Ya existe un vehiculo con esa placa")
    db.refresh(vehiculo)
    return vehiculo