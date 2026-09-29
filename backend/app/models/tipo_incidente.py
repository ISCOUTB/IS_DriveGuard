# models/tipo_incidente.py
"""
Modelo ORM de TipoIncidente (SQLAlchemy).
Catalogo de tipos de senal de fatiga detectables, con su umbral configurable (RF-16 / RNF de sensibilidad).
"""
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.evento import Evento


class TipoIncidente(Base):
    __tablename__ = "tipos_incidentes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4
    )
    
    nombre: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True
    )
    
    descripcion: Mapped[
        Optional[str]] = mapped_column(Text)
    umbral_sensibilidad: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    unidad_medida: Mapped[Optional[str]] = mapped_column(String(20))

    eventos: Mapped[list["Evento"]] = relationship(back_populates="tipo_incidente")