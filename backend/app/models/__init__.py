# models/__init__.py
from app.models.base import Base
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.models.tipo_incidente import TipoIncidente
from app.models.sesion import Sesion
from app.models.evento import Evento

__all__ = ["Base", "Usuario", "Vehiculo", "TipoIncidente", "Sesion", "Evento"]