"""
Esquemas Pydantic de Vehicle (request/response de la API).
"""
# schemas/vehiculo.py
"""
Esquemas Pydantic de Vehiculo (request/response de la API).
"""
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.vehiculo import EstadoVehiculoEnum, TipoVehiculoEnum


class VehiculoBase(BaseModel):
    placa: str = Field(max_length=10)
    tipo_vehiculo: TipoVehiculoEnum
    marca: Optional[str] = Field(default=None, max_length=50)
    modelo: Optional[str] = Field(default=None, max_length=50)


class VehiculoCreate(VehiculoBase):
    pass


class VehiculoUpdate(BaseModel):
    placa: Optional[str] = Field(default=None, max_length=10)
    tipo_vehiculo: Optional[TipoVehiculoEnum] = None
    marca: Optional[str] = Field(default=None, max_length=50)
    modelo: Optional[str] = Field(default=None, max_length=50)
    estado: Optional[EstadoVehiculoEnum] = None


class VehiculoRead(VehiculoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    estado: EstadoVehiculoEnum
