"""
Traduce las excepciones de dominio de los servicios a respuestas HTTP.
Asi los routers no necesitan try/except repetidos.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.errors import (
    ConflictoError,
    NoEncontradoError,
    PermisoError,
    ReglaNegocioError,
)

_CODIGOS = (
    (NoEncontradoError, 404),
    (ConflictoError, 409),
    (ReglaNegocioError, 422),
    (PermisoError, 403),
)


def _fabricar_handler(codigo: int):
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=codigo, content={"detail": str(exc)})

    return handler


def register_exception_handlers(app: FastAPI) -> None:
    for excepcion, codigo in _CODIGOS:
        app.add_exception_handler(excepcion, _fabricar_handler(codigo))