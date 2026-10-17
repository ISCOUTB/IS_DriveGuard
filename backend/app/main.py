"""
Punto de entrada de la aplicacion FastAPI.
Corresponde al issue "Esqueleto del proyecto FastAPI" (Sprint 1).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, events, usuario, vehicles
from app.core.config import settings

app = FastAPI(
    title="Driver Fatigue Detection API",
    description="API para el sistema de deteccion de fatiga y somnolencia en conduccion.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(usuario.router)
app.include_router(vehicles.router)
app.include_router(events.router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Endpoint de salud usado para verificar que el servicio esta corriendo."""
    return {"status": "ok"}
