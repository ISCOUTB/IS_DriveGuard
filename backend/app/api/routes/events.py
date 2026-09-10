"""
Rutas de eventos de fatiga. Cubre RF9 (ingesta de eventos) y RF10/RF13/RF14
(consulta y filtrado de incidentes para el dashboard).
"""
from fastapi import APIRouter

router = APIRouter(prefix="/events", tags=["events"])

# TODO: implementar POST /events (ingesta desde el modulo de CV) y
# GET /events?driver=&date=&type= (consulta filtrada para el dashboard).
