from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.dependencias import obtener_ahora
from app.services.resumen import resumen_del_dia as calcular_resumen


router = APIRouter(prefix="/api/alarmas")


# Información de las alarmas por hora
class AlarmaPorHora(BaseModel):
    hora: str
    cantidad: int


# Información general del resumen diario
class ResumenDiario(BaseModel):
    fecha: date
    total: int
    por_hora: list[AlarmaPorHora]


# Obtener el resumen diario de alarmas
@router.get("/resumen-dia", response_model=ResumenDiario)
def consultar_resumen(
    conexion_bd: Session = Depends(obtener_sesion),
    fecha_actual: datetime = Depends(obtener_ahora)
):
    return calcular_resumen(conexion_bd, fecha_actual)