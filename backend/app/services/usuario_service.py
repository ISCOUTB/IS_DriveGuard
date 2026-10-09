"""
Logica de negocio de usuarios: alta, consulta y actualizacion.
Las reglas que la base de datos no puede garantizar por si sola viven aqui.
"""
import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.usuario import RolEnum, Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


class ConflictoError(Exception):
    """El recurso ya existe (correo o licencia duplicados). La ruta lo traduce a 409."""


class ReglaNegocioError(Exception):
    """La operacion viola una regla de negocio. La ruta lo traduce a 422."""


def crear_usuario(db: Session, datos: UsuarioCreate) -> Usuario:
    if db.scalar(select(Usuario.id).where(Usuario.correo == datos.correo)):
        raise ConflictoError("Ya existe un usuario con ese correo")
    if datos.numero_licencia and db.scalar(
        select(Usuario.id).where(Usuario.numero_licencia == datos.numero_licencia)
    ):
        raise ConflictoError("Ya existe un usuario con ese numero de licencia")

    usuario = Usuario(
        nombre_completo=datos.nombre_completo,
        correo=datos.correo,
        contrasena_hash=hash_password(datos.password),
        rol=datos.rol,
        telefono=datos.telefono,
        numero_licencia=datos.numero_licencia,
        fecha_vinculacion=datos.fecha_vinculacion,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        # Carrera entre dos altas simultaneas con el mismo correo/licencia.
        db.rollback()
        raise ConflictoError("Correo o numero de licencia ya registrados")
    db.refresh(usuario)
    return usuario


def obtener_usuario(db: Session, usuario_id: uuid.UUID) -> Optional[Usuario]:
    return db.get(Usuario, usuario_id)


def listar_usuarios(
    db: Session,
    rol: Optional[RolEnum] = None,
    activo: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
) -> Sequence[Usuario]:
    consulta = select(Usuario).order_by(Usuario.nombre_completo)
    if rol is not None:
        consulta = consulta.where(Usuario.rol == rol)
    if activo is not None:
        consulta = consulta.where(Usuario.activo == activo)
    return db.scalars(consulta.offset(skip).limit(limit)).all()


def actualizar_usuario(db: Session, usuario: Usuario, datos: UsuarioUpdate) -> Usuario:
    cambios = datos.model_dump(exclude_unset=True)

    campos_conductor = {"numero_licencia", "fecha_vinculacion"}
    if usuario.rol != RolEnum.DRIVER and campos_conductor & cambios.keys():
        raise ReglaNegocioError(
            "numero_licencia y fecha_vinculacion solo aplican a conductores"
        )
    if usuario.rol == RolEnum.DRIVER:
        for campo in campos_conductor:
            if campo in cambios and cambios[campo] is None:
                raise ReglaNegocioError(f"{campo} es obligatorio para un conductor")

    nueva_licencia = cambios.get("numero_licencia")
    if nueva_licencia and nueva_licencia != usuario.numero_licencia:
        if db.scalar(select(Usuario.id).where(Usuario.numero_licencia == nueva_licencia)):
            raise ConflictoError("Ya existe un usuario con ese numero de licencia")

    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictoError("Numero de licencia ya registrado")
    db.refresh(usuario)
    return usuario