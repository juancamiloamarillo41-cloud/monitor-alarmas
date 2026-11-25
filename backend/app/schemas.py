"""Contrato de la API (modelos de respuesta Pydantic)."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.services.clasificacion import NivelAlerta


class NivelFiltro(StrEnum):
    TODOS = "TODOS"
    NORMAL = "NORMAL"
    WARN = "WARN"
    CRITICO = "CRITICO"


class AlarmaRespuesta(BaseModel):
    id_alarma: int
    tecnologia_2g: int
    tecnologia_3g: int
    tecnologia_4g: int
    fecha_creacion: datetime = Field(description="Fecha de creación con zona horaria (America/Bogota).")
    municipio: str
    departamento: str
    notificada: str
    duracion_segundos: int = Field(description="Tiempo transcurrido desde la creación hasta `consultado_en`.")
    duracion_texto: str = Field(examples=["3d 04h 12m"])
    nivel: NivelAlerta


class ConteoNiveles(BaseModel):
    """Totales por nivel sobre TODAS las alarmas (independiente del filtro aplicado)."""

    todos: int
    normal: int
    warn: int
    critico: int


class ListaAlarmasRespuesta(BaseModel):
    consultado_en: datetime = Field(description="Momento usado para calcular duraciones y niveles.")
    nivel: NivelFiltro
    total: int = Field(description="Cantidad de alarmas en `items` (después del filtro).")
    conteo: ConteoNiveles
    items: list[AlarmaRespuesta]


class ErrorFilaRespuesta(BaseModel):
    linea: int
    motivo: str


class ResultadoImportacionRespuesta(BaseModel):
    nombre_archivo: str
    insertadas: int
    actualizadas: int
    rechazadas: int
    errores: list[ErrorFilaRespuesta] = Field(description="Detalle de las primeras filas rechazadas.")
    errores_omitidos: int = Field(description="Filas rechazadas que no se detallan en `errores` por el límite.")
