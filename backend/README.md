# Backend

API REST del sistema, construida con FastAPI y PostgreSQL.

## Estructura

- `app/core/` — configuracion, conexion a base de datos y seguridad.
- `app/models/` — modelos ORM (SQLAlchemy), una tabla por archivo.
- `app/schemas/` — modelos Pydantic de request/response, separados de los
  modelos ORM para no exponer columnas internas por la API.
- `app/api/routes/` — un router por recurso, calcado del contrato en
  `docs/openapi.yaml`.
- `app/services/` — logica de negocio que no es simplemente CRUD.
- `alembic/` — migraciones versionadas del esquema de la base de datos.
- `tests/` — pruebas con pytest.

## Como correr localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Como correr con Docker

Desde la raiz del repositorio:

```bash
docker-compose up
```

## Como correr las pruebas

```bash
pytest
```

## Migraciones (Alembic)

```bash
alembic revision --autogenerate -m "descripcion del cambio"
alembic upgrade head
```
