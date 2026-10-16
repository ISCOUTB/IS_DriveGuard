"""
Fixtures compartidas para las pruebas del backend.

Usa SQLite en memoria e inyecta la sesion de prueba en lugar de la sesion
real via ``dependency_overrides`` de FastAPI, de modo que ``pytest`` corre
sin necesidad de PostgreSQL.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models.base import Base


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _crear_usuario_en_db(db_session, *, correo, password, rol, **extras):
    """Alta directa en BD (evita pasar por POST /usuarios que exige ser admin)."""
    from app.models.usuario import Usuario
    from app.schemas.usuario import UsuarioCreate
    from app.services.usuario_service import crear_usuario

    datos = UsuarioCreate(
        nombre_completo=extras.get("nombre_completo", "Usuario Prueba"),
        correo=correo,
        password=password,
        rol=rol,
        numero_licencia=extras.get("numero_licencia"),
        fecha_vinculacion=extras.get("fecha_vinculacion"),
    )
    return crear_usuario(db_session, datos)


@pytest.fixture()
def admin_usuario(db_session):
    from app.models.usuario import RolEnum

    return _crear_usuario_en_db(
        db_session,
        correo="admin@test.com",
        password="ClaveSegura123",
        rol=RolEnum.ADMIN,
    )


@pytest.fixture()
def conductor_usuario(db_session):
    import datetime

    from app.models.usuario import RolEnum

    return _crear_usuario_en_db(
        db_session,
        correo="conductor@test.com",
        password="ClaveSegura123",
        rol=RolEnum.DRIVER,
        numero_licencia="LIC-001",
        fecha_vinculacion=datetime.date(2024, 1, 15),
    )


def _login(client, correo, password):
    respuesta = client.post(
        "/auth/login", json={"correo": correo, "password": password}
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]


@pytest.fixture()
def admin_headers(client, admin_usuario):
    token = _login(client, "admin@test.com", "ClaveSegura123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def conductor_headers(client, conductor_usuario):
    token = _login(client, "conductor@test.com", "ClaveSegura123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sesion_y_tipo(db_session, conductor_usuario):
    """Crea un vehiculo, una sesion activa y un tipo de incidente de prueba."""
    import datetime

    from app.models.sesion import Sesion
    from app.models.tipo_incidente import TipoIncidente
    from app.models.vehiculo import TipoVehiculoEnum, Vehiculo

    vehiculo = Vehiculo(
        id=uuid.uuid4(), placa="ABC123", tipo_vehiculo=TipoVehiculoEnum.BUS
    )
    db_session.add(vehiculo)
    db_session.commit()
    db_session.refresh(vehiculo)

    sesion = Sesion(
        id=uuid.uuid4(),
        conductor_id=conductor_usuario.id,
        vehiculo_id=vehiculo.id,
        fecha_hora_inicio=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(sesion)
    tipo = TipoIncidente(
        id=uuid.uuid4(),
        nombre="cierre_ojos",
        descripcion="Cierre prolongado de ojos",
        umbral_sensibilidad=2.0,
        unidad_medida="segundos",
    )
    db_session.add(tipo)
    db_session.commit()
    db_session.refresh(sesion)
    db_session.refresh(tipo)
    return sesion, tipo
