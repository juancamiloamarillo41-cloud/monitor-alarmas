# Monitor de Alarmas — Prueba técnica Full Stack

Aplicación web que importa un CSV de alarmas, las clasifica por criticidad (NORMAL / WARN / CRÍTICO) en el backend y las muestra en una tabla con indicadores visuales, filtros, exportación a Excel y un resumen del día por hora.

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2 · SQLite |
| Frontend | React 19 · TypeScript · Vite · exceljs |
| Comunicación | API REST con JSON; frontend y backend son proyectos independientes |

## Funcionalidades

- **Importación desde la web** de un CSV separado por `|` (UTF-8, Windows-1252 o UTF-16). Se valida cada fila: ID entero positivo, 2G/3G/4G entre −100 y 100, fecha en formato Oracle, `NOTIFICADA` S o N y municipio y departamento obligatorios. Las filas inválidas se rechazan una por una (con línea y motivo) sin detener la importación; reimportar un archivo actualiza los registros existentes por `ID_ALARMA`.
- **Tabla** con toda la información importada y la **duración acumulada** de cada alarma (desde su creación hasta el momento de la consulta). Se refresca sola cada minuto.
- **Clasificación en el backend** (ver la regla más abajo). Las filas se distinguen por color y etiqueta según el nivel.
- **Filtros**: Todos, WARN, CRÍTICO y Normales, con el conteo de cada nivel.
- **Exportación a Excel** de exactamente las filas y columnas visibles (respeta el filtro y el orden).
- **Resumen del día**: modal con las alarmas creadas hoy, agrupadas hora por hora.

### Regla de clasificación

Una alarma cumple las **condiciones base** si:

1. Al menos una tecnología (2G, 3G, 4G) está disponible, es decir, tiene un valor ≥ 0 (−100 = no disponible).
2. **Todas** las tecnologías disponibles valen exactamente 100.
3. `NOTIFICADA = 'N'`.

Si las cumple, el nivel depende del tiempo transcurrido desde `FECHA_CREACION`:

| Duración | Nivel |
|----------|-------|
| ≤ 1 h | NORMAL |
| > 1 h y ≤ 24 h | WARN |
| > 24 h | CRÍTICO |

Si no las cumple, la alarma es NORMAL. Las fechas se interpretan en la zona horaria America/Bogota. El nivel no se guarda en la base de datos: se calcula en cada consulta, porque cambia con el paso del tiempo.

## Requisitos

- Python 3.12 o superior
- Node.js 20 o superior

## Puesta en marcha

Se necesitan dos terminales, una para cada proyecto.

### Backend (http://localhost:8000)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

La documentación interactiva de la API (Swagger) queda en http://localhost:8000/docs. La base de datos SQLite (`backend/alarmas.db`) se crea al iniciar.

### Frontend (http://localhost:5173)

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

La URL del backend se configura en `frontend/.env` (`VITE_API_URL`). El backend solo acepta peticiones (CORS) desde `http://localhost:5173`; si cambias el puerto del frontend, ajusta `CORS_ORIGENES` en `backend/.env` en formato JSON, por ejemplo `CORS_ORIGENES=["http://localhost:3000"]`.

### Uso

1. Abre http://localhost:5173.
2. En **Importar alarmas**, selecciona `data/muestra_datos.csv` y pulsa **Importar**.
3. Usa los filtros, **Exportar a Excel** y **Resumen del día**.

## Datos de demostración

La muestra de la prueba tiene fechas de septiembre a noviembre de 2026, así que hoy todas sus alarmas salen CRÍTICO o NORMAL y ninguna es del día actual. Para ver los tres niveles y el resumen del día, genera un archivo con fechas recientes:

```powershell
python data/generar_datos_demo.py
```

Crea `data/datos_demo.csv` (no se versiona) e imprime los niveles esperados y las alarmas de hoy por hora, para compararlos con lo que muestra la aplicación. Opciones: `--salida`, `--semilla`, `--por-hora`. Solo usa la biblioteca estándar de Python.

Como los niveles dependen del tiempo, importa el archivo poco después de generarlo.

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/salud` | Comprueba que la API está en marcha |
| `POST` | `/api/alarmas/importar` | Importa un CSV (`multipart/form-data`, campo `archivo`). Responde con insertadas, actualizadas, rechazadas y el detalle de hasta 100 errores |
| `GET` | `/api/alarmas?nivel=TODOS\|WARN\|CRITICO\|NORMAL` | Alarmas clasificadas en el momento de la consulta, ordenadas por gravedad y antigüedad, con el conteo por nivel |
| `GET` | `/api/alarmas/resumen-dia` | Alarmas creadas hoy, agrupadas por hora |
| `DELETE` | `/api/alarmas` | Elimina todas las alarmas (para reiniciar la demostración) |

Respuestas de error: `400` (archivo no válido), `413` (archivo de más de 10 MB), `422` (parámetros inválidos) y `500` con un JSON `{"detail": ...}` ante un error inesperado. El detalle de cada respuesta está en Swagger.

## Estructura

```
backend/
  app/
    main.py              FastAPI: CORS, routers y creación de tablas
    config.py            Configuración por variables de entorno (.env)
    db.py, models.py     Conexión y modelo SQLAlchemy
    schemas.py           Contrato de la API (Pydantic)
    dependencias.py      Reloj inyectable (obtener_ahora)
    routers/             Endpoints REST
    services/
      clasificacion.py   Regla de negocio (funciones puras)
      importador.py      Lectura y validación del CSV, upsert
      alarmas.py         Consulta y filtrado de alarmas clasificadas
      resumen.py         Resumen del día por hora
frontend/
  src/
    api.ts, types.ts     Cliente tipado de la API
    columnas.ts          Columnas de la tabla (también las usa el Excel)
    exportarExcel.ts     Exportación de las filas visibles
    hooks/useAlarmas.ts  Carga, filtro y refresco automático
    components/          Importación, filtros, tabla y modal de resumen
data/
  muestra_datos.csv      Muestra entregada con la prueba
  generar_datos_demo.py  Generador de datos con fechas recientes
```
