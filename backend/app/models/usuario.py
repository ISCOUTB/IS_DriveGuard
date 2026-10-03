"""
Modelo ORM de Usuario (SQLAlchemy).
Representa a cualquier persona que puede iniciar sesión en el sistema:
conductor, supervisor de flota o administrador.
"""
import datetime
import enum
import uuid
from typing import Optional, TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
if TYPE_CHECKING:
    from app.models.sesion import Sesion # type: ignore

class RolEnum(str, enum.Enum):
    """El rol de un usuario solo puede ser administrador, conductor o supervisor."""
    ADMIN = "administrador"
    DRIVER = "conductor"
    SUPERVISOR = "supervisor"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    nombre_completo: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    correo: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
    )

    contrasena_hash: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    rol: Mapped[RolEnum] = mapped_column(
        Enum(RolEnum, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
    )

    activo: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    fecha_creacion: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )

    numero_licencia: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
    )

    telefono: Mapped[Optional[str]] = mapped_column(
        String(20),
    )

    fecha_vinculacion: Mapped[Optional[datetime.date]] = mapped_column(
        Date,
    )

    sesiones: Mapped[list["Sesion"]] = relationship(back_populates="conductor")
    
    __table_args__ = (
        CheckConstraint(
            "(rol = 'conductor' AND numero_licencia IS NOT NULL AND fecha_vinculacion IS NOT NULL) "
            "OR (rol <> 'conductor')",
            name="ck_usuario_campos_conductor",
        ),
    )