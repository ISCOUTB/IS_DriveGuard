"""
Logica de negocio de vehiculos: alta, consulta, actualizacion y baja.
Las violaciones de unicidad (placa) se senalan con ConflictoError (la ruta
lo traduce a 409); los intentos de borrar un vehiculo con sesiones asociadas
se senalan con ReglaNegocioError (la ruta lo traduce a 409/422).
"""
import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.vehiculo import Vehiculo
from app.schemas.vehiculo import VehiculoCreate, VehiculoUpdate


class ConflictoError(Exception):
    """El recurso ya existe (placa duplicada). La ruta lo traduce a 409."""


class ReglaNegocioError(Exception):
    """La operacion viola una regla de negocio. La ruta lo traduce a 409/422."""


def crear_vehiculo(db: Session, datos: VehiculoCreate) -> Vehiculo:
    if db.scalar(select(Vehiculo.id).where(Vehiculo.placa == datos.placa)):
        raise ConflictoError("Ya existe un vehiculo con esa placa")
    vehiculo = Vehiculo(
        placa=datos.placa,
        tipo_vehiculo=datos.tipo_vehiculo,
        marca=datos.marca,
        modelo=datos.modelo,
    )
    db.add(vehiculo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictoError("Ya existe un vehiculo con esa placa")
    db.refresh(vehiculo)
    return vehiculo


def obtener_vehiculo(db: Session, vehiculo_id: uuid.UUID) -> Optional[Vehiculo]:
    return db.get(Vehiculo, vehiculo_id)


def listar_vehiculos(
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> Sequence[Vehiculo]:
    consulta = select(Vehiculo).order_by(Vehiculo.placa).offset(skip).limit(limit)
    return db.scalars(consulta).all()


def actualizar_vehiculo(
    db: Session, vehiculo: Vehiculo, datos: VehiculoUpdate
) -> Vehiculo:
    cambios = datos.model_dump(exclude_unset=True)
    nueva_placa = cambios.get("placa")
    if nueva_placa and nueva_placa != vehiculo.placa:
        if db.scalar(select(Vehiculo.id).where(Vehiculo.placa == nueva_placa)):
            raise ConflictoError("Ya existe un vehiculo con esa placa")
    for campo, valor in cambios.items():
        setattr(vehiculo, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictoError("Ya existe un vehiculo con esa placa")
    db.refresh(vehiculo)
    return vehiculo


def eliminar_vehiculo(db: Session, vehiculo: Vehiculo) -> None:
    db.delete(vehiculo)
    try:
        db.commit()
    except IntegrityError:
        # RESTRICT en sesiones.vehiculo_id: no se puede borrar con historial.
        db.rollback()
        raise ReglaNegocioError(
            "No se puede eliminar el vehiculo porque tiene sesiones asociadas"
        )
