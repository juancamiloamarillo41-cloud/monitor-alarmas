"""Endpoints de importación, consulta y limpieza de alarmas."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import obtener_sesion
from app.dependencias import obtener_ahora
from app.schemas import (
    AlarmaRespuesta,
    ConteoNiveles,
    ErrorFilaRespuesta,
    ListaAlarmasRespuesta,
    NivelFiltro,
    ResultadoImportacionRespuesta,
)
from app.services.alarmas import AlarmaClasificada, consultar_alarmas, eliminar_todas
from app.services.clasificacion import NivelAlerta, formatear_duracion
from app.services.importador import ArchivoInvalidoError, importar_csv

router = APIRouter(prefix="/api/alarmas", tags=["alarmas"])

SesionDep = Annotated[Session, Depends(obtener_sesion)]
AhoraDep = Annotated[datetime, Depends(obtener_ahora)]

MAX_ERRORES_DETALLADOS = 100


@router.post(
    "/importar",
    response_model=ResultadoImportacionRespuesta,
    summary="Importar un CSV de alarmas separado por '|'",
    responses={
        400: {"description": "Archivo vacío, sin extensión .csv o con cabecera inválida"},
        413: {"description": "Archivo demasiado grande"},
    },
)
def importar(archivo: UploadFile, sesion: SesionDep) -> ResultadoImportacionRespuesta:
    # `def` (no `async def`): leer, validar y guardar es trabajo síncrono; FastAPI lo ejecuta
    # en un hilo aparte y el servidor sigue atendiendo otras peticiones mientras tanto.
    nombre = archivo.filename or ""
    if not nombre.lower().endswith(".csv"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El archivo debe tener extensión .csv.")

    limite = settings.tamano_maximo_archivo_mb * 1024 * 1024
    contenido = archivo.file.read(limite + 1)
    if len(contenido) > limite:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"El archivo supera el máximo de {settings.tamano_maximo_archivo_mb} MB.",
        )

    try:
        resultado = importar_csv(sesion, contenido)
    except ArchivoInvalidoError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from None

    return ResultadoImportacionRespuesta(
        nombre_archivo=nombre,
        insertadas=resultado.insertadas,
        actualizadas=resultado.actualizadas,
        rechazadas=resultado.rechazadas,
        errores=[ErrorFilaRespuesta(linea=e.linea, motivo=e.motivo) for e in resultado.errores[:MAX_ERRORES_DETALLADOS]],
        errores_omitidos=max(resultado.rechazadas - MAX_ERRORES_DETALLADOS, 0),
    )


@router.get(
    "",
    response_model=ListaAlarmasRespuesta,
    summary="Listar alarmas clasificadas por criticidad",
)
def listar(
    sesion: SesionDep,
    ahora: AhoraDep,
    nivel: Annotated[NivelFiltro, Query(description="Filtra por nivel de alerta.")] = NivelFiltro.TODOS,
) -> ListaAlarmasRespuesta:
    filtro = None if nivel == NivelFiltro.TODOS else NivelAlerta(nivel.value)
    consulta = consultar_alarmas(sesion, ahora, settings.tz, filtro)

    return ListaAlarmasRespuesta(
        consultado_en=ahora,
        nivel=nivel,
        total=len(consulta.items),
        conteo=ConteoNiveles(
            todos=consulta.total_general,
            normal=consulta.conteo[NivelAlerta.NORMAL],
            warn=consulta.conteo[NivelAlerta.WARN],
            critico=consulta.conteo[NivelAlerta.CRITICO],
        ),
        items=[_a_respuesta(item) for item in consulta.items],
    )


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar todas las alarmas (útil para reiniciar la demostración)",
)
def vaciar(sesion: SesionDep) -> Response:
    eliminar_todas(sesion)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _a_respuesta(item: AlarmaClasificada) -> AlarmaRespuesta:
    alarma = item.alarma
    return AlarmaRespuesta(
        id_alarma=alarma.id_alarma,
        tecnologia_2g=alarma.tecnologia_2g,
        tecnologia_3g=alarma.tecnologia_3g,
        tecnologia_4g=alarma.tecnologia_4g,
        fecha_creacion=item.fecha_creacion,
        municipio=alarma.municipio,
        departamento=alarma.departamento,
        notificada=alarma.notificada,
        duracion_segundos=int(item.duracion.total_seconds()),
        duracion_texto=formatear_duracion(item.duracion),
        nivel=item.nivel,
    )
