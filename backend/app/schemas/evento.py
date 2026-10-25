# schemas/evento.py
"""
Esquemas Pydantic de Evento (request/response de la API).
"""
import datetime
import uuid
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.evento import SeveridadEnum


class EventoBase(BaseModel):
    tipo_incidente_id: uuid.UUID
    fecha_hora: datetime.datetime
    duracion_segundos: float = Field(gt=0, lt=1000)
    severidad: SeveridadEnum
    valor_metrica: float = Field(gt=-1000, lt=1000)


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


class EventoLoteCreate(BaseModel):
    """Cola offline del cliente de captura: se envia en un solo request (RNF-02)."""
    eventos: List[EventoCreate] = Field(min_length=1, max_length=500)


class EventoLoteResultado(BaseModel):
    recibidos: int
    creados: int
    duplicados: int


class ResumenConductor(BaseModel):
    conductor_id: uuid.UUID
    nombre_completo: str
    total: int


class ResumenEventos(BaseModel):
    """Agregaciones para el dashboard."""
    total: int
    por_tipo: Dict[str, int]
    por_severidad: Dict[str, int]
    por_dia: Dict[str, int]
    por_conductor: List[ResumenConductor]