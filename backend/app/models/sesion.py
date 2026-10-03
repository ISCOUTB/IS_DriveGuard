# models/sesion.py
"""
Modelo ORM de Sesion (turno de conduccion).
Conecta un Usuario (rol conductor) con un Vehiculo durante un periodo de tiempo.
"""
import datetime
import enum
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.evento import Evento
    from app.models.usuario import Usuario
    from app.models.vehiculo import Vehiculo


class EstadoSesionEnum(str, enum.Enum):
    ACTIVA = "activa"
    FINALIZADA = "finalizada"


class Sesion(Base):
    __tablename__ = "sesiones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conductor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False
    )
    vehiculo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vehiculos.id", ondelete="RESTRICT"), nullable=False
    )
    fecha_hora_inicio: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    fecha_hora_fin: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    estado: Mapped[EstadoSesionEnum] = mapped_column(
        Enum(EstadoSesionEnum, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=EstadoSesionEnum.ACTIVA,
    )

    conductor: Mapped["Usuario"] = relationship(back_populates="sesiones")
    vehiculo: Mapped["Vehiculo"] = relationship(back_populates="sesiones")
    eventos: Mapped[list["Evento"]] = relationship(back_populates="sesion")