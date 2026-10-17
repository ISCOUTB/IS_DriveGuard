"""
Configuracion centralizada de la aplicacion, cargada desde variables de
entorno (o desde .env en desarrollo local).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Driver Fatigue Detection API"
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/fatigue_detection"
    )
    SECRET_KEY: str = "change-this-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]


settings = Settings()
