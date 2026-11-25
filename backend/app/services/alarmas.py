"""Consulta de alarmas clasificadas en un momento dado.

El nivel depende del tiempo transcurrido, así que no se guarda: se calcula al
consultar, y el filtro por nivel se aplica en Python después de clasificar.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Alarma
from app.services.clasificacion import NivelAlerta, calcular_duracion, calcular_nivel

# Orden de la tabla: primero lo más grave.
_PRIORIDAD = {NivelAlerta.CRITICO: 0, NivelAlerta.WARN: 1, NivelAlerta.NORMAL: 2}


@dataclass(frozen=True)
class AlarmaClasificada:
    alarma: Alarma
    fecha_creacion: datetime  # con zona horaria
    duracion: timedelta
    nivel: NivelAlerta


@dataclass(frozen=True)
class ConsultaAlarmas:
    items: list[AlarmaClasificada]
    conteo: dict[NivelAlerta, int]

    @property
    def total_general(self) -> int:
        return sum(self.conteo.values())


def clasificar(alarma: Alarma, ahora: datetime, zona: tzinfo) -> AlarmaClasificada:
    """`ahora` debe tener zona horaria; la fecha guardada se interpreta en `zona`."""
    fecha_creacion = alarma.fecha_creacion.replace(tzinfo=zona)
    return AlarmaClasificada(
        alarma=alarma,
        fecha_creacion=fecha_creacion,
        duracion=calcular_duracion(fecha_creacion, ahora),
        nivel=calcular_nivel(
            alarma.tecnologia_2g,
            alarma.tecnologia_3g,
            alarma.tecnologia_4g,
            alarma.notificada,
            fecha_creacion,
            ahora,
        ),
    )


def consultar_alarmas(
    sesion: Session,
    ahora: datetime,
    zona: tzinfo,
    nivel: NivelAlerta | None = None,
) -> ConsultaAlarmas:
    """Clasifica todas las alarmas y devuelve las del `nivel` pedido (o todas si es None).

    El conteo por nivel siempre se calcula sobre el total, para los contadores de los filtros.
    """
    clasificadas = [clasificar(alarma, ahora, zona) for alarma in sesion.scalars(select(Alarma))]

    conteo = dict.fromkeys(NivelAlerta, 0)
    for item in clasificadas:
        conteo[item.nivel] += 1

    items = [item for item in clasificadas if nivel is None or item.nivel == nivel]
    items.sort(key=lambda item: (_PRIORIDAD[item.nivel], -item.duracion, item.alarma.id_alarma))

    return ConsultaAlarmas(items=items, conteo=conteo)


def eliminar_todas(sesion: Session) -> int:
    resultado = sesion.execute(delete(Alarma))
    sesion.commit()
    return resultado.rowcount
