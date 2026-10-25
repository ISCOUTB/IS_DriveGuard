"""
Convencion de fechas del backend: todo se guarda en UTC y sin zona horaria
(las columnas son DateTime sin tz). Estas funciones normalizan lo que llega del cliente.
"""
import datetime
from typing import Optional


def ahora_utc() -> datetime.datetime:
    """Hora actual en UTC, sin tzinfo."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def a_utc_naive(valor: Optional[datetime.datetime]) -> Optional[datetime.datetime]:
    """
    Si la fecha trae zona horaria, la convierte a UTC y quita el tzinfo.
    Si no la trae, se asume que ya esta en UTC.
    """
    if valor is None:
        return None
    if valor.tzinfo is not None:
        return valor.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return valor