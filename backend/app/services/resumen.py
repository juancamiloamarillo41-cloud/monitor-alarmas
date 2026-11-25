from datetime import timedelta
from sqlalchemy import select
from app.models import Alarma


def resumen_del_dia(sesion, ahora):

    # Obtener el inicio y el final del día
    inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    fin = inicio + timedelta(days=1)

    # Consultar las alarmas creadas hoy
    consulta = select(Alarma.fecha_creacion).where(
        Alarma.fecha_creacion >= inicio,
        Alarma.fecha_creacion < fin
    )

    fechas = sesion.scalars(consulta).all()

    # Contar las alarmas de cada hora
    cantidades = [0] * 24

    for fecha in fechas:
        cantidades[fecha.hour] += 1

    # Crear el resumen por hora
    por_hora = []

    for hora in range(24):
        por_hora.append({
            "hora": f"{hora:02d}:00",
            "cantidad": cantidades[hora]
        })

    # Devolver los resultados
    return {
        "fecha": inicio.date(),
        "total": len(fechas),
        "por_hora": por_hora
    }