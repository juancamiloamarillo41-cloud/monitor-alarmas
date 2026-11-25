"""Configuración de la aplicación, leída de variables de entorno o de backend/.env."""

from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./alarmas.db"
    zona_horaria: str = "America/Bogota"
    cors_origenes: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    tamano_maximo_archivo_mb: int = 10

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.zona_horaria)


settings = Settings()
