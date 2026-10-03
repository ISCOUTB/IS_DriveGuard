
"""
Modelo ORM de Evento (incidente de fatiga detectado).

El id NO lleva default: se genera en el cliente de captura (Raspberry Pi) antes
de encolarse localmente (RNF-02), para que el backend pueda insertar con
ON CONFLICT (id) DO NOTHING y evitar duplicados si el cliente reintenta el envio.
"""
import datetime
import enum
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.sesion import Sesion
    from app.models.tipo_incidente import TipoIncidente


class SeveridadEnum(str, enum.Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class Evento(Base):
    __tablename__ = "eventos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    sesion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sesiones.id", ondelete="RESTRICT"), nullable=False
    )
    tipo_incidente_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tipos_incidentes.id", ondelete="RESTRICT"), nullable=False
    )
    fecha_hora: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    fecha_recepcion: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    duracion_segundos: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    severidad: Mapped[SeveridadEnum] = mapped_column(
        Enum(SeveridadEnum, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    valor_metrica: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    comentario_conductor: Mapped[Optional[str]] = mapped_column(Text)
    revisado: Mapped[bool] = mapped_column(nullable=False, default=False)

    sesion: Mapped["Sesion"] = relationship(back_populates="eventos")
    tipo_incidente: Mapped["TipoIncidente"] = relationship(back_populates="eventos")