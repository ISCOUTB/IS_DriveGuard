# schemas/sesion.py
"""
Esquemas Pydantic de Sesion (request/response de la API).
"""
import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.sesion import EstadoSesionEnum


class SesionBase(BaseModel):
    conductor_id: uuid.UUID
    vehiculo_id: uuid.UUID


class SesionCreate(SesionBase):
    pass


class SesionUpdate(BaseModel):
    fecha_hora_fin: Optional[datetime.datetime] = None
    estado: Optional[EstadoSesionEnum] = None


class SesionRead(SesionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fecha_hora_inicio: datetime.datetime
    fecha_hora_fin: Optional[datetime.datetime] = None
    estado: EstadoSesionEnum