# schemas/tipo_incidente.py
"""
Esquemas Pydantic de TipoIncidente (request/response de la API).
"""
import uuid
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TipoIncidenteBase(BaseModel):
    nombre: str = Field(max_length=50)
    descripcion: Optional[str] = None
    unidad_medida: Optional[str] = Field(default=None, max_length=20)


class TipoIncidenteCreate(TipoIncidenteBase):
    umbral_sensibilidad: Decimal = Field(gt=0)


class TipoIncidenteUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, max_length=50)
    descripcion: Optional[str] = None
    umbral_sensibilidad: Optional[Decimal] = Field(default=None, gt=0)
    unidad_medida: Optional[str] = Field(default=None, max_length=20)


class TipoIncidenteRead(TipoIncidenteBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    umbral_sensibilidad: Decimal