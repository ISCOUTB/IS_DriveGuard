"""
Configuracion de la conexion a la base de datos con SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.models.base import Base

from app.core.config import settings


def _normalizar_url(url: str) -> str:
    # SQLAlchemy 2.x usa psycopg (v3) por defecto para "postgresql://", pero el
    # proyecto declara psycopg2-binary; se fija el driver para no exigir psycopg.
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


engine = create_engine(_normalizar_url(settings.DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def get_db():
    """Dependencia de FastAPI que entrega una sesion de base de datos por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
