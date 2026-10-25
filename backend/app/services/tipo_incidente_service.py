"""
Logica de negocio del catalogo de tipos de incidente y sus umbrales de sensibilidad.
"""
import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.tipo_incidente import TipoIncidente
from app.schemas.tipo_incidente import TipoIncidenteCreate, TipoIncidenteUpdate
from app.services.errors import ConflictoError, NoEncontradoError, ReglaNegocioError


def _nombre_en_uso(db: Session, nombre: str, excluir_id: Optional[uuid.UUID] = None) -> bool:
    consulta = select(TipoIncidente.id).where(TipoIncidente.nombre == nombre)
    if excluir_id is not None:
        consulta = consulta.where(TipoIncidente.id != excluir_id)
    return db.scalar(consulta) is not None


def crear_tipo(db: Session, datos: TipoIncidenteCreate) -> TipoIncidente:
    nombre = datos.nombre.strip()
    if _nombre_en_uso(db, nombre):
        raise ConflictoError("Ya existe un tipo de incidente con ese nombre")
    tipo = TipoIncidente(
        nombre=nombre,
        descripcion=datos.descripcion,
        umbral_sensibilidad=datos.umbral_sensibilidad,
        unidad_medida=datos.unidad_medida,
    )
    db.add(tipo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictoError("Ya existe un tipo de incidente con ese nombre")
    db.refresh(tipo)
    return tipo


def obtener_tipo(db: Session, tipo_id: uuid.UUID) -> TipoIncidente:
    tipo = db.get(TipoIncidente, tipo_id)
    if tipo is None:
        raise NoEncontradoError("Tipo de incidente no encontrado")
    return tipo


def listar_tipos(db: Session) -> Sequence[TipoIncidente]:
    return db.scalars(select(TipoIncidente).order_by(TipoIncidente.nombre)).all()


def actualizar_tipo(db: Session, tipo_id: uuid.UUID, datos: TipoIncidenteUpdate) -> TipoIncidente:
    tipo = obtener_tipo(db, tipo_id)
    cambios = datos.model_dump(exclude_unset=True)

    for campo in ("nombre", "umbral_sensibilidad"):
        if campo in cambios and cambios[campo] is None:
            raise ReglaNegocioError(f"{campo} no puede ser nulo")

    if "nombre" in cambios:
        cambios["nombre"] = cambios["nombre"].strip()
        if _nombre_en_uso(db, cambios["nombre"], excluir_id=tipo.id):
            raise ConflictoError("Ya existe un tipo de incidente con ese nombre")

    for campo, valor in cambios.items():
        setattr(tipo, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictoError("Ya existe un tipo de incidente con ese nombre")
    db.refresh(tipo)
    return tipo