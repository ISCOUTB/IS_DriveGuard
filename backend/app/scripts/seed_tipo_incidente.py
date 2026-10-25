"""
Carga el catalogo inicial de tipos de incidente. Es idempotente: omite los que ya existen.
Los umbrales son valores de partida; se ajustan despues con PATCH /tipos-incidentes/{id}.

Uso (desde backend/):
    python -m app.scripts.seed_tipos_incidentes
Dentro de Docker:
    docker-compose exec backend python -m app.scripts.seed_tipos_incidentes
"""
import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.tipo_incidente import TipoIncidente

TIPOS_INICIALES = [
    {
        "nombre": "Somnolencia ocular",
        "descripcion": "Cierre prolongado de los ojos (EAR por debajo del umbral).",
        "umbral_sensibilidad": 0.25,
        "unidad_medida": "EAR",
    },
    {
        "nombre": "Bostezo",
        "descripcion": "Apertura sostenida de la boca (MAR por encima del umbral).",
        "umbral_sensibilidad": 0.60,
        "unidad_medida": "MAR",
    },
    {
        "nombre": "Cabeceo",
        "descripcion": "Inclinacion de la cabeza hacia adelante por encima del umbral.",
        "umbral_sensibilidad": 15.00,
        "unidad_medida": "grados",
    },
]


def main() -> int:
    creados = 0
    with SessionLocal() as db:
        for datos in TIPOS_INICIALES:
            if db.scalar(select(TipoIncidente.id).where(TipoIncidente.nombre == datos["nombre"])):
                continue
            db.add(TipoIncidente(**datos))
            creados += 1
        db.commit()
    print(f"Tipos de incidente creados: {creados} (existentes omitidos: {len(TIPOS_INICIALES) - creados}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())