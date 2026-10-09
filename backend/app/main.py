"""
Punto de entrada de la aplicacion FastAPI.
Corresponde al issue "Esqueleto del proyecto FastAPI" (Sprint 1).
"""
from fastapi import FastAPI

from app.api.routes import auth

app = FastAPI(
    title="Driver Fatigue Detection API",
    description="API para el sistema de deteccion de fatiga y somnolencia en conduccion.",
    version="0.1.0",
)

app.include_router(auth.router)

# Pendientes de implementar:
# from app.api.routes import drivers, vehicles, events
# app.include_router(drivers.router)
# app.include_router(vehicles.router)
# app.include_router(events.router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Endpoint de salud usado para verificar que el servicio esta corriendo."""
    return {"status": "ok"}