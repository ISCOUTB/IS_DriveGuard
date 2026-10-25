"""
Excepciones de dominio compartidas por los servicios.
Los servicios las lanzan sin conocer HTTP; app/api/errors.py las traduce a respuestas.
"""


class NoEncontradoError(Exception):
    """El recurso solicitado no existe (404)."""


class ConflictoError(Exception):
    """El recurso ya existe o el estado actual impide la operacion (409)."""


class ReglaNegocioError(Exception):
    """La operacion viola una regla de negocio (422)."""


class PermisoError(Exception):
    """El usuario autenticado no puede realizar la operacion sobre ese recurso (403)."""