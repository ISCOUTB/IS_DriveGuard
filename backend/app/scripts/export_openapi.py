"""
Exporta el contrato de la API a docs/openapi.json, para compartirlo con el modulo
de CV y el frontend. Vuelve a ejecutarlo cada vez que cambien los endpoints.

Uso (desde backend/):
    python -m app.scripts.export_openapi
"""
import json
from pathlib import Path

from app.main import app

DESTINO = Path(__file__).resolve().parents[3] / "docs" / "openapi.json"


def main() -> None:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Contrato exportado a {DESTINO}")


if __name__ == "__main__":
    main()