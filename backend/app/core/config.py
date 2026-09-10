"""
Configuracion centralizada de la aplicacion, cargada desde variables de
entorno (o desde .env en desarrollo local).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Driver Fatigue Detection API"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/fatigue_detection"
    SECRET_KEY: str = "change-this-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


settings = Settings()
