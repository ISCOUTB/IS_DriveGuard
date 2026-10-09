"""
Rutas de gestion de usuarios (administradores, supervisores y conductores).
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.usuario import RolEnum, Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioRead, UsuarioUpdate
from app.services import usuario_service
from app.services.usuario_service import ConflictoError, ReglaNegocioError

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

# Campos que un usuario puede editar sobre su propio perfil.
CAMPOS_PERFIL_PROPIO = {"nombre_completo", "telefono"}


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    datos: UsuarioCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(RolEnum.ADMIN)),
) -> Usuario:
    """Crea un usuario de cualquier rol. Solo administrador."""
    try:
        return usuario_service.crear_usuario(db, datos)
    except ConflictoError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=List[UsuarioRead])
def listar_usuarios(
    rol: Optional[RolEnum] = None,
    activo: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_roles(RolEnum.ADMIN, RolEnum.SUPERVISOR)),
) -> list:
    """Lista usuarios. El supervisor solo ve conductores."""
    if actual.rol == RolEnum.SUPERVISOR:
        if rol not in (None, RolEnum.DRIVER):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sin permisos para ese rol")
        rol = RolEnum.DRIVER
    return list(usuario_service.listar_usuarios(db, rol, activo, skip, limit))


def _obtener_o_404(db: Session, usuario_id: uuid.UUID) -> Usuario:
    usuario = usuario_service.obtener_usuario(db, usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


@router.get("/{usuario_id}", response_model=UsuarioRead)
def obtener_usuario(
    usuario_id: uuid.UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
) -> Usuario:
    """Administrador: cualquiera. Supervisor: conductores. Cualquiera: su propio perfil."""
    objetivo = _obtener_o_404(db, usuario_id)
    es_propio = objetivo.id == actual.id
    es_admin = actual.rol == RolEnum.ADMIN
    supervisa = actual.rol == RolEnum.SUPERVISOR and objetivo.rol == RolEnum.DRIVER
    if not (es_propio or es_admin or supervisa):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sin permisos sobre este usuario")
    return objetivo


@router.patch("/{usuario_id}", response_model=UsuarioRead)
def actualizar_usuario(
    usuario_id: uuid.UUID,
    datos: UsuarioUpdate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
) -> Usuario:
    """
    Administrador: edita cualquier campo (incluida la baja con activo=false).
    Otros roles: solo nombre_completo y telefono de su propio perfil.
    """
    objetivo = _obtener_o_404(db, usuario_id)
    cambios = datos.model_dump(exclude_unset=True)

    if actual.rol == RolEnum.ADMIN:
        if objetivo.id == actual.id and cambios.get("activo") is False:
            raise HTTPException(
                422,
                detail="Un administrador no puede desactivarse a si mismo",
            )
    else:
        if objetivo.id != actual.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sin permisos sobre este usuario")
        if not cambios.keys() <= CAMPOS_PERFIL_PROPIO:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Solo puedes editar tu nombre y telefono",
            )
    try:
        return usuario_service.actualizar_usuario(db, objetivo, datos)
    except ConflictoError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))
    except ReglaNegocioError as e:
        raise HTTPException(422, detail=str(e))