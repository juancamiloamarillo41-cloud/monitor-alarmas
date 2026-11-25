import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import crear_tablas
from app.routers import alarmas, resumen


# Preparar la aplicación al iniciar
@asynccontextmanager
async def ciclo_de_vida(app):
    crear_tablas()
    yield


# Crear la API
app = FastAPI(
    title="API de Alarmas",
    description="Importación, clasificación y resumen de alarmas.",
    version="0.2.0",
    lifespan=ciclo_de_vida
)


# Registrar errores
logger = logging.getLogger(__name__)


@app.middleware("http")
async def manejar_errores(request, call_next):
    try:
        respuesta = await call_next(request)
        return respuesta

    except Exception:
        logger.exception("Error en la API")

        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"}
        )


# Configurar permisos de acceso
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origenes,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Comprobar si la API funciona
@app.get("/api/salud")
def salud():
    return {"estado": "ok"}


# Conectar las rutas de la aplicación
app.include_router(alarmas.router)
app.include_router(resumen.router)
