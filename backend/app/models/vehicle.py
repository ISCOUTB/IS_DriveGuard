"""
Modelo ORM de Vehiculo (SQLAlchemy).
"""
import enum
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from models.sesion import Sesion


class TipoVehiculoEnum(str, enum.Enum):
    BUS = "bus"
    CAMION_CARGA = "camion_carga"


class EstadoVehiculoEnum(str, enum.Enum):
    ACTIVO = "activo"
    MANTENIMIENTO = "mantenimiento"
    INACTIVO = "inactivo"


class Vehiculo(Base):
    __tablename__ = "vehiculos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    placa: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)

    tipo_vehiculo: Mapped[TipoVehiculoEnum] = mapped_column(
        Enum(TipoVehiculoEnum, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
    )

    marca: Mapped[Optional[str]] = mapped_column(String(50))

    modelo: Mapped[Optional[str]] = mapped_column(String(50))

    estado: Mapped[EstadoVehiculoEnum] = mapped_column(
        Enum(EstadoVehiculoEnum, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
        default=EstadoVehiculoEnum.ACTIVO,
    )

    sesiones: Mapped[list["Sesion"]] = relationship(back_populates="vehiculo")