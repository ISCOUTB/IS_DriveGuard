"""
Punto de entrada de la aplicacion FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routes import auth, eventos, sesiones, tipos_incidentes, usuarios, vehiculos
from app.core.config import settings

app = FastAPI(
    title="Driver Fatigue Detection API",
    description="API para el sistema de deteccion de fatiga y somnolencia en conduccion.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(vehiculos.router)
app.include_router(tipos_incidentes.router)
app.include_router(sesiones.router)
app.include_router(eventos.router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Endpoint de salud usado para verificar que el servicio esta corriendo."""
    return {"status": "ok"}