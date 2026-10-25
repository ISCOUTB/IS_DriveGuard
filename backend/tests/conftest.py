"""
Fixtures compartidas: base SQLite en memoria (una nueva por prueba), cliente HTTP con
la sesion de BD inyectada, y fabricas de usuarios/datos con token JWT directo
(sin pasar por /auth/login, para no pagar el costo de bcrypt en cada prueba).
"""
import os

# Debe ir antes de importar la app: evita que se cree un engine apuntando a PostgreSQL.
# Por defecto las pruebas usan SQLite en memoria. Para correrlas contra PostgreSQL real:
#   TEST_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/fatigue_test pytest
# (la base DEBE llamarse *_test: la suite borra y recrea todas las tablas).
_url = os.environ.get("TEST_DATABASE_URL", "sqlite://")
if not _url.startswith("sqlite") and not _url.rsplit("/", 1)[-1].endswith("_test"):
    raise RuntimeError("TEST_DATABASE_URL debe apuntar a una base cuyo nombre termine en _test")
os.environ["DATABASE_URL"] = _url

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Base, TipoIncidente, Usuario, Vehiculo
from app.models.usuario import RolEnum
from app.models.vehiculo import TipoVehiculoEnum

PASSWORD = "ClaveSegura1"
HASH_PASSWORD = hash_password(PASSWORD)  # bcrypt es lento: se calcula una sola vez


@pytest.fixture()
def db():
    url = os.environ["DATABASE_URL"]
    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    else:
        engine = create_engine(url)
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    SessionTest = sessionmaker(bind=engine, autoflush=False)
    session = SessionTest()

    def _get_db():
        s = SessionTest()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _get_db
    yield session
    session.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db):
    return TestClient(app)


@pytest.fixture()
def crear_usuario(db):
    """Fabrica: crear_usuario(RolEnum.DRIVER, correo=..., activo=...) -> Usuario."""

    def _crear(rol: RolEnum, correo=None, activo=True, **extra):
        sufijo = uuid.uuid4().hex[:6]
        datos = dict(
            nombre_completo=f"{rol.value} {sufijo}",
            correo=correo or f"{rol.value}-{sufijo}@test.com",
            contrasena_hash=HASH_PASSWORD,
            rol=rol,
            activo=activo,
        )
        if rol == RolEnum.DRIVER:
            import datetime

            datos.setdefault("numero_licencia", f"LIC-{sufijo}")
            datos.setdefault("fecha_vinculacion", datetime.date(2026, 1, 1))
        datos.update(extra)
        usuario = Usuario(**datos)
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario

    return _crear


@pytest.fixture()
def auth():
    """auth(usuario) -> headers con un JWT valido para ese usuario."""

    def _auth(usuario: Usuario) -> dict:
        token = create_access_token(str(usuario.id), usuario.rol.value)
        return {"Authorization": f"Bearer {token}"}

    return _auth


@pytest.fixture()
def admin(crear_usuario):
    return crear_usuario(RolEnum.ADMIN)


@pytest.fixture()
def supervisor(crear_usuario):
    return crear_usuario(RolEnum.SUPERVISOR)


@pytest.fixture()
def conductor(crear_usuario):
    return crear_usuario(RolEnum.DRIVER)


@pytest.fixture()
def vehiculo(db):
    v = Vehiculo(placa="ABC123", tipo_vehiculo=TipoVehiculoEnum.BUS)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@pytest.fixture()
def tipo(db):
    t = TipoIncidente(nombre="Somnolencia ocular", umbral_sensibilidad=0.25, unidad_medida="EAR")
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture()
def sesion(client, auth, conductor, vehiculo):
    """Sesion activa del fixture `conductor` con el fixture `vehiculo`."""
    r = client.post(
        "/sesiones",
        headers=auth(conductor),
        json={"conductor_id": str(conductor.id), "vehiculo_id": str(vehiculo.id)},
    )
    assert r.status_code == 201, r.text
    return r.json()