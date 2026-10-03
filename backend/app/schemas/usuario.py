# schemas/usuario.py
"""
Esquemas Pydantic de Usuario (request/response de la API).
"""
import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.usuario import RolEnum


class UsuarioBase(BaseModel):
    nombre_completo: str = Field(max_length=150)
    correo: EmailStr
    telefono: Optional[str] = Field(default=None, max_length=20)


class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=8)
    rol: RolEnum
    numero_licencia: Optional[str] = Field(default=None, max_length=50)
    fecha_vinculacion: Optional[datetime.date] = None

    @model_validator(mode="after")
    def validar_campos_conductor(self) -> "UsuarioCreate":
        if self.rol == RolEnum.DRIVER:
            if not self.numero_licencia or not self.fecha_vinculacion:
                raise ValueError(
                    "numero_licencia y fecha_vinculacion son obligatorios cuando rol = 'conductor'"
                )
        return self


class UsuarioUpdate(BaseModel):
    nombre_completo: Optional[str] = Field(default=None, max_length=150)
    telefono: Optional[str] = Field(default=None, max_length=20)
    numero_licencia: Optional[str] = Field(default=None, max_length=50)
    fecha_vinculacion: Optional[datetime.date] = None
    activo: Optional[bool] = None


class UsuarioRead(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rol: RolEnum
    activo: bool
    fecha_creacion: datetime.datetime
    numero_licencia: Optional[str] = None
    fecha_vinculacion: Optional[datetime.date] = None