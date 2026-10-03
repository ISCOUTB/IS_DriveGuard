"""
Esquemas Pydantic de Event (request/response de la API).
"""
# schemas/evento.py
"""
Esquemas Pydantic de Evento (request/response de la API).
"""
import datetime
import uuid
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from models.evento import SeveridadEnum


class EventoBase(BaseModel):
    tipo_incidente_id: uuid.UUID
    fecha_hora: datetime.datetime
    duracion_segundos: Decimal = Field(gt=0)
    severidad: SeveridadEnum
    valor_metrica: Decimal


class EventoCreate(EventoBase):
    id: uuid.UUID  # generado en el cliente de captura, no en el servidor
    sesion_id: uuid.UUID
    comentario_conductor: Optional[str] = None


class EventoUpdate(BaseModel):
    comentario_conductor: Optional[str] = None
    revisado: Optional[bool] = None


class EventoRead(EventoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sesion_id: uuid.UUID
    fecha_recepcion: datetime.datetime
    comentario_conductor: Optional[str] = None
    revisado: bool
