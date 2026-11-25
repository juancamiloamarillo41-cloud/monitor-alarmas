"""Modelo de persistencia de las alarmas.

`fecha_creacion` se guarda sin zona horaria (SQLite no la soporta) y se interpreta
siempre en la zona configurada (`settings.zona_horaria`). El nivel de alerta y la
duración NO se guardan: dependen del momento de la consulta y se calculan al leer.
"""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Alarma(Base):
    __tablename__ = "alarmas"

    id_alarma: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    tecnologia_2g: Mapped[int]
    tecnologia_3g: Mapped[int]
    tecnologia_4g: Mapped[int]
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, index=True)
    municipio: Mapped[str] = mapped_column(String(150))
    departamento: Mapped[str] = mapped_column(String(150))
    notificada: Mapped[str] = mapped_column(String(1))

    def __repr__(self) -> str:
        return f"Alarma(id_alarma={self.id_alarma}, fecha_creacion={self.fecha_creacion:%Y-%m-%d %H:%M:%S})"
