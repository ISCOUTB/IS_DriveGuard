"""
Configuracion de la conexion a la base de datos con SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI que entrega una sesion de base de datos por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
