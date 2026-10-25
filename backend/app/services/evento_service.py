"""
Logica de negocio de eventos: ingesta idempotente desde el cliente de captura
(RNF-02, cola offline), consulta filtrada y agregaciones para el dashboard.
"""
import datetime
import uuid
from typing import Dict, List, Optional, Sequence, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.tiempo import a_utc_naive
from app.models.evento import Evento, SeveridadEnum
from app.models.sesion import Sesion
from app.models.tipo_incidente import TipoIncidente
from app.models.usuario import RolEnum, Usuario
from app.schemas.evento import EventoCreate, EventoUpdate
from app.services.errors import ConflictoError, NoEncontradoError, PermisoError, ReglaNegocioError


# --------------------------------------------------------------------------- ingesta

def _insert_ignorando_duplicados(db: Session):
    """INSERT ... ON CONFLICT DO NOTHING segun el motor (PostgreSQL en produccion, SQLite en pruebas)."""
    motor = db.get_bind().dialect.name
    if motor == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    elif motor == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        raise RuntimeError(f"Motor de base de datos no soportado para la ingesta: {motor}")
    return insert


def _validar_referencias(db: Session, eventos: Sequence[EventoCreate], actual: Usuario) -> None:
    """Verifica que las sesiones y tipos existan y que un conductor solo escriba en sus sesiones."""
    sesion_ids = {e.sesion_id for e in eventos}
    sesiones = {
        s.id: s for s in db.scalars(select(Sesion).where(Sesion.id.in_(sesion_ids))).all()
    }
    faltan = sesion_ids - sesiones.keys()
    if faltan:
        raise NoEncontradoError(f"Sesion no encontrada: {sorted(str(i) for i in faltan)[0]}")
    if actual.rol == RolEnum.DRIVER:
        for sesion in sesiones.values():
            if sesion.conductor_id != actual.id:
                raise PermisoError("Solo puedes registrar eventos en tus propias sesiones")

    tipo_ids = {e.tipo_incidente_id for e in eventos}
    existentes = set(
        db.scalars(select(TipoIncidente.id).where(TipoIncidente.id.in_(tipo_ids))).all()
    )
    faltan_tipos = tipo_ids - existentes
    if faltan_tipos:
        raise NoEncontradoError(
            f"Tipo de incidente no encontrado: {sorted(str(i) for i in faltan_tipos)[0]}"
        )


def _insertar(db: Session, datos: EventoCreate) -> bool:
    """Inserta el evento. Devuelve True si se creo, False si el id ya existia."""
    insert = _insert_ignorando_duplicados(db)
    resultado = db.execute(
        insert(Evento)
        .values(
            id=datos.id,
            sesion_id=datos.sesion_id,
            tipo_incidente_id=datos.tipo_incidente_id,
            fecha_hora=a_utc_naive(datos.fecha_hora),
            duracion_segundos=datos.duracion_segundos,
            severidad=datos.severidad,
            valor_metrica=datos.valor_metrica,
            comentario_conductor=datos.comentario_conductor,
            revisado=False,
        )
        .on_conflict_do_nothing(index_elements=["id"])
    )
    return resultado.rowcount == 1


def _verificar_duplicado(db: Session, datos: EventoCreate) -> Evento:
    """Un reintento legitimo repite el mismo id y la misma sesion; cualquier otro caso es un choque de ids."""
    existente = db.get(Evento, datos.id)
    if existente is None or existente.sesion_id != datos.sesion_id:
        raise ConflictoError("El id del evento ya esta en uso por otro evento")
    return existente


def registrar_evento(db: Session, datos: EventoCreate, actual: Usuario) -> Tuple[Evento, bool]:
    """
    Registra un evento de forma idempotente.
    Devuelve (evento, creado): creado=False si el cliente reenvio un evento ya recibido.
    """
    _validar_referencias(db, [datos], actual)
    creado = _insertar(db, datos)
    if not creado:
        db.rollback()
        return _verificar_duplicado(db, datos), False
    db.commit()
    return db.get(Evento, datos.id), True


def registrar_lote(db: Session, eventos: Sequence[EventoCreate], actual: Usuario) -> Dict[str, int]:
    """
    Registra varios eventos en una sola transaccion (vaciado de la cola offline).
    Si alguno es invalido, no se guarda ninguno y el cliente puede reintentar el lote completo.
    """
    ids = [e.id for e in eventos]
    if len(set(ids)) != len(ids):
        raise ReglaNegocioError("El lote contiene ids de evento repetidos")

    _validar_referencias(db, eventos, actual)
    creados = 0
    for datos in eventos:
        if _insertar(db, datos):
            creados += 1
        else:
            _verificar_duplicado(db, datos)
    db.commit()
    return {"recibidos": len(eventos), "creados": creados, "duplicados": len(eventos) - creados}


# --------------------------------------------------------------------------- consulta

def _condiciones(
    actual: Usuario,
    conductor_id: Optional[uuid.UUID] = None,
    vehiculo_id: Optional[uuid.UUID] = None,
    sesion_id: Optional[uuid.UUID] = None,
    tipo_incidente_id: Optional[uuid.UUID] = None,
    severidad: Optional[SeveridadEnum] = None,
    revisado: Optional[bool] = None,
    desde: Optional[datetime.datetime] = None,
    hasta: Optional[datetime.datetime] = None,
) -> list:
    """Condiciones WHERE comunes (requieren JOIN con Sesion). Un conductor solo ve lo suyo."""
    if actual.rol == RolEnum.DRIVER:
        if conductor_id not in (None, actual.id):
            raise PermisoError("Un conductor solo puede consultar sus propios eventos")
        conductor_id = actual.id

    condiciones = []
    if conductor_id is not None:
        condiciones.append(Sesion.conductor_id == conductor_id)
    if vehiculo_id is not None:
        condiciones.append(Sesion.vehiculo_id == vehiculo_id)
    if sesion_id is not None:
        condiciones.append(Evento.sesion_id == sesion_id)
    if tipo_incidente_id is not None:
        condiciones.append(Evento.tipo_incidente_id == tipo_incidente_id)
    if severidad is not None:
        condiciones.append(Evento.severidad == severidad)
    if revisado is not None:
        condiciones.append(Evento.revisado == revisado)
    if desde is not None:
        condiciones.append(Evento.fecha_hora >= a_utc_naive(desde))
    if hasta is not None:
        condiciones.append(Evento.fecha_hora <= a_utc_naive(hasta))
    return condiciones


def listar_eventos(db: Session, actual: Usuario, skip: int = 0, limit: int = 50, **filtros) -> Sequence[Evento]:
    consulta = (
        select(Evento)
        .join(Sesion, Evento.sesion_id == Sesion.id)
        .where(*_condiciones(actual, **filtros))
        .order_by(Evento.fecha_hora.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(consulta).all()


def obtener_evento(db: Session, evento_id: uuid.UUID, actual: Usuario) -> Evento:
    evento = db.get(Evento, evento_id)
    if evento is None:
        raise NoEncontradoError("Evento no encontrado")
    if actual.rol == RolEnum.DRIVER:
        sesion = db.get(Sesion, evento.sesion_id)
        if sesion is None or sesion.conductor_id != actual.id:
            raise PermisoError("Sin permisos sobre este evento")
    return evento


# Que campos puede modificar cada rol: el conductor comenta, el supervisor revisa.
_CAMPOS_EDITABLES = {
    RolEnum.DRIVER: {"comentario_conductor"},
    RolEnum.SUPERVISOR: {"revisado"},
    RolEnum.ADMIN: {"comentario_conductor", "revisado"},
}


def actualizar_evento(db: Session, evento_id: uuid.UUID, datos: EventoUpdate, actual: Usuario) -> Evento:
    evento = obtener_evento(db, evento_id, actual)
    cambios = datos.model_dump(exclude_unset=True)

    no_permitidos = cambios.keys() - _CAMPOS_EDITABLES[actual.rol]
    if no_permitidos:
        raise PermisoError(f"Tu rol no puede modificar: {', '.join(sorted(no_permitidos))}")
    if "revisado" in cambios and cambios["revisado"] is None:
        raise ReglaNegocioError("revisado no puede ser nulo")

    for campo, valor in cambios.items():
        setattr(evento, campo, valor)
    db.commit()
    db.refresh(evento)
    return evento


# --------------------------------------------------------------------------- dashboard

def resumen_eventos(db: Session, actual: Usuario, **filtros) -> dict:
    """Totales por tipo, severidad, dia y conductor, con los mismos filtros que el listado."""
    condiciones = _condiciones(actual, **filtros)

    def agrupar(columna, *joins):
        consulta = select(columna, func.count(Evento.id)).join(Sesion, Evento.sesion_id == Sesion.id)
        for destino, condicion in joins:
            consulta = consulta.join(destino, condicion)
        return db.execute(consulta.where(*condiciones).group_by(columna)).all()

    total = db.scalar(
        select(func.count(Evento.id)).join(Sesion, Evento.sesion_id == Sesion.id).where(*condiciones)
    )
    por_tipo = agrupar(TipoIncidente.nombre, (TipoIncidente, Evento.tipo_incidente_id == TipoIncidente.id))
    por_severidad = agrupar(Evento.severidad)
    por_dia = agrupar(func.date(Evento.fecha_hora))

    por_conductor = []
    if actual.rol != RolEnum.DRIVER:
        filas = db.execute(
            select(Usuario.id, Usuario.nombre_completo, func.count(Evento.id))
            .join(Sesion, Evento.sesion_id == Sesion.id)
            .join(Usuario, Sesion.conductor_id == Usuario.id)
            .where(*condiciones)
            .group_by(Usuario.id, Usuario.nombre_completo)
            .order_by(func.count(Evento.id).desc())
        ).all()
        por_conductor = [
            {"conductor_id": f[0], "nombre_completo": f[1], "total": f[2]} for f in filas
        ]

    return {
        "total": total or 0,
        "por_tipo": {nombre: n for nombre, n in por_tipo},
        "por_severidad": {(s.value if hasattr(s, "value") else str(s)): n for s, n in por_severidad},
        "por_dia": {str(dia): n for dia, n in sorted(por_dia, key=lambda f: str(f[0]))},
        "por_conductor": por_conductor,
    }