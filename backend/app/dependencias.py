"""Dependencias compartidas por los routers (se pueden sustituir en las pruebas)."""

from datetime import datetime

from app.config import settings


def obtener_ahora() -> datetime:
    """Momento actual en la zona horaria configurada."""
    return datetime.now(settings.tz)
