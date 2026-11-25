"""Conexión a la base de datos y sesión por petición."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Base

_es_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    # SQLite: FastAPI puede atender la petición en un hilo distinto al que abrió la conexión.
    connect_args={"check_same_thread": False} if _es_sqlite else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def crear_tablas() -> None:
    Base.metadata.create_all(bind=engine)


def obtener_sesion() -> Iterator[Session]:
    """Dependencia de FastAPI: abre una sesión por petición y la cierra al terminar."""
    sesion = SessionLocal()
    try:
        yield sesion
    finally:
        sesion.close()
