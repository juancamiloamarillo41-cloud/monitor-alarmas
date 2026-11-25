"""Reglas de negocio: clasificación de alarmas por criticidad.

Funciones puras (sin base de datos ni reloj del sistema): el momento actual se
recibe como parámetro para que el resultado sea determinista y fácil de probar.

Regla:

- Una tecnología (2G, 3G, 4G) está *disponible* si su valor es >= 0.
- Condiciones base: al menos una tecnología disponible, TODAS las disponibles
  valen exactamente 100 y la alarma no está notificada (NOTIFICADA = 'N').
- Si cumple las condiciones base:
    duración > 24 h          -> CRITICO
    1 h < duración <= 24 h   -> WARN
    duración <= 1 h          -> NORMAL
- Si no las cumple -> NORMAL.
"""

from datetime import datetime, timedelta
from enum import StrEnum

UNA_HORA = timedelta(hours=1)
VEINTICUATRO_HORAS = timedelta(hours=24)
CAPACIDAD_AL_LIMITE = 100
NO_NOTIFICADA = "N"


class NivelAlerta(StrEnum):
    NORMAL = "NORMAL"
    WARN = "WARN"
    CRITICO = "CRITICO"


def tecnologias_disponibles(*valores: int) -> list[int]:
    """Valores de las tecnologías disponibles (>= 0)."""
    return [valor for valor in valores if valor >= 0]


def cumple_condiciones_base(tecnologia_2g: int, tecnologia_3g: int, tecnologia_4g: int, notificada: str) -> bool:
    disponibles = tecnologias_disponibles(tecnologia_2g, tecnologia_3g, tecnologia_4g)
    return (
        len(disponibles) > 0
        and all(valor == CAPACIDAD_AL_LIMITE for valor in disponibles)
        and notificada == NO_NOTIFICADA
    )


def calcular_duracion(fecha_creacion: datetime, ahora: datetime) -> timedelta:
    """Tiempo transcurrido desde la creación. Una fecha futura cuenta como 0.

    Ambas fechas deben ser del mismo tipo (las dos con zona horaria o las dos sin ella).
    """
    return max(ahora - fecha_creacion, timedelta(0))


def nivel_por_duracion(duracion: timedelta) -> NivelAlerta:
    """Nivel según el tiempo activo, para una alarma que ya cumple las condiciones base."""
    if duracion > VEINTICUATRO_HORAS:
        return NivelAlerta.CRITICO
    if duracion > UNA_HORA:
        return NivelAlerta.WARN
    return NivelAlerta.NORMAL


def calcular_nivel(
    tecnologia_2g: int,
    tecnologia_3g: int,
    tecnologia_4g: int,
    notificada: str,
    fecha_creacion: datetime,
    ahora: datetime,
) -> NivelAlerta:
    if not cumple_condiciones_base(tecnologia_2g, tecnologia_3g, tecnologia_4g, notificada):
        return NivelAlerta.NORMAL
    return nivel_por_duracion(calcular_duracion(fecha_creacion, ahora))


def formatear_duracion(duracion: timedelta) -> str:
    """Duración legible: '3d 04h 12m' o '04h 12m' si es menor a un día."""
    minutos_totales = int(duracion.total_seconds()) // 60
    dias, resto = divmod(minutos_totales, 24 * 60)
    horas, minutos = divmod(resto, 60)
    if dias:
        return f"{dias}d {horas:02d}h {minutos:02d}m"
    return f"{horas:02d}h {minutos:02d}m"
