"""Importación del CSV de alarmas (separado por '|').

Flujo: bytes -> texto -> filas validadas -> upsert en BD por ID_ALARMA.
Las filas inválidas se rechazan individualmente (con línea y motivo) sin
detener la importación del resto. Un archivo sin la cabecera
esperada se rechaza completo con `ArchivoInvalidoError`.
"""

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import Session

from app.models import Alarma

SEPARADOR = "|"

COLUMNAS = ("ID_ALARMA", "2G", "3G", "4G", "FECHA_CREACION", "MUNICIPIO", "DEPARTAMENTO", "NOTIFICADA")

VALORES_NOTIFICADA = {"S", "N"}

# Rangos válidos: las tecnologías son porcentajes, con -100 = no disponible;
# el ID debe caber en un entero de 64 bits con signo (límite de SQLite y PostgreSQL BIGINT).
VALOR_TECNOLOGIA_MIN, VALOR_TECNOLOGIA_MAX = -100, 100
ID_MAXIMO = 2**63 - 1

_PATRON_ENTERO = re.compile(r"^-?\d+$")
_CARACTERES_DE_CONTROL = re.compile(r"[\x00-\x1f\x7f]")

MESES = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}  # fmt: skip

# Formato Oracle 'DD-MON-RR HH.MI.SS.FF AM', p. ej. '09-OCT-26 10.12.56.000000000 PM'
_PATRON_FECHA = re.compile(
    r"^(?P<dia>\d{1,2})-(?P<mes>[A-Za-z]{3})-(?P<anio>\d{2}|\d{4}) "
    r"(?P<hora>\d{1,2})\.(?P<minuto>\d{2})\.(?P<segundo>\d{2})(?:\.(?P<fraccion>\d{1,9}))? "
    r"(?P<meridiano>AM|PM)$",
    re.IGNORECASE,
)

# Tamaños de lote: SQLite limita los parámetros por sentencia (999 en versiones antiguas).
_LOTE_CONSULTA = 500  # 1 parámetro por ID
_LOTE_ESCRITURA = 100  # 8 parámetros por fila

# Upsert nativo de cada motor soportado (`INSERT ... ON CONFLICT DO UPDATE`).
_INSERT_POR_MOTOR = {"sqlite": sqlite.insert, "postgresql": postgresql.insert}


class ArchivoInvalidoError(ValueError):
    """El archivo no se puede procesar (vacío, codificación o cabecera incorrecta)."""


@dataclass(frozen=True)
class AlarmaCSV:
    id_alarma: int
    tecnologia_2g: int
    tecnologia_3g: int
    tecnologia_4g: int
    fecha_creacion: datetime
    municipio: str
    departamento: str
    notificada: str


@dataclass(frozen=True)
class ErrorFila:
    linea: int
    motivo: str


@dataclass
class ResultadoParseo:
    registros: list[AlarmaCSV] = field(default_factory=list)
    errores: list[ErrorFila] = field(default_factory=list)


@dataclass
class ResultadoImportacion:
    insertadas: int
    actualizadas: int
    rechazadas: int
    errores: list[ErrorFila]


# --------------------------------------------------------------------------- #
# Conversión de valores
# --------------------------------------------------------------------------- #


def parsear_fecha_oracle(texto: str) -> datetime:
    """Convierte '09-OCT-26 10.12.56.000000000 PM' en datetime (sin zona horaria).

    - Mes en inglés, sin depender del *locale* del sistema.
    - Año de 2 dígitos con la regla RR de Oracle: 00–49 -> 2000–2049, 50–99 -> 1950–1999.
    - La fracción se trunca a microsegundos (Python no maneja nanosegundos).
    """
    coincidencia = _PATRON_FECHA.match(texto.strip())
    if not coincidencia:
        raise ValueError(f"formato de fecha no reconocido: '{texto}'")

    partes = coincidencia.groupdict()
    mes = MESES.get(partes["mes"].upper())
    if mes is None:
        raise ValueError(f"mes no reconocido: '{partes['mes']}'")

    anio = int(partes["anio"])
    if len(partes["anio"]) == 2:
        anio += 2000 if anio < 50 else 1900

    hora_12 = int(partes["hora"])
    if not 1 <= hora_12 <= 12:
        raise ValueError(f"hora fuera de rango en formato de 12 horas: {hora_12}")
    hora = hora_12 % 12 + (12 if partes["meridiano"].upper() == "PM" else 0)

    microsegundos = int((partes["fraccion"] or "0").ljust(9, "0")[:6])

    # datetime(...) valida día, minutos y segundos (p. ej. 31-FEB lanza ValueError).
    return datetime(anio, mes, int(partes["dia"]), hora, int(partes["minuto"]), int(partes["segundo"]), microsegundos)


def formatear_fecha_oracle(fecha: datetime) -> str:
    """Operación inversa de `parsear_fecha_oracle` (se ignora la zona horaria)."""
    mes = next(abreviatura for abreviatura, numero in MESES.items() if numero == fecha.month)
    hora_12 = fecha.hour % 12 or 12
    meridiano = "PM" if fecha.hour >= 12 else "AM"
    return (
        f"{fecha.day:02d}-{mes}-{fecha.year % 100:02d} "
        f"{hora_12:02d}.{fecha.minute:02d}.{fecha.second:02d}.{fecha.microsecond:06d}000 {meridiano}"
    )


def _entero(valor: str, columna: str, minimo: int, maximo: int) -> int:
    """Solo dígitos con signo opcional '-' (int() aceptaría '1_00' o '+5') y dentro del rango."""
    texto = valor.strip()
    if not _PATRON_ENTERO.match(texto):
        raise ValueError(f"{columna} debe ser un número entero (valor: '{valor}')")
    numero = int(texto)
    if not minimo <= numero <= maximo:
        raise ValueError(f"{columna} debe estar entre {minimo} y {maximo} (valor: {numero})")
    return numero


def _texto_obligatorio(valor: str, columna: str) -> str:
    texto = valor.strip()
    if not texto:
        raise ValueError(f"{columna} es obligatorio")
    return texto


def decodificar(contenido: bytes) -> str:
    """UTF-16 si trae BOM; si no, UTF-8 (con o sin BOM) y, si falla, Windows-1252 (Excel en Windows)."""
    if contenido.startswith((b"\xff\xfe", b"\xfe\xff")):
        codificaciones = ("utf-16",)
    else:
        codificaciones = ("utf-8-sig", "cp1252")
    for codificacion in codificaciones:
        try:
            return contenido.decode(codificacion)
        except UnicodeDecodeError:
            continue
    raise ArchivoInvalidoError("No se reconoce la codificación del archivo. Guárdalo como CSV UTF-8 e inténtalo de nuevo.")


# --------------------------------------------------------------------------- #
# Lectura del CSV
# --------------------------------------------------------------------------- #


def _validar_cabecera(cabecera: list[str] | None) -> dict[str, int]:
    """Devuelve la posición de cada columna. Admite cualquier orden y mayúsculas/minúsculas."""
    if not cabecera or all(not celda.strip() for celda in cabecera):
        raise ArchivoInvalidoError("El archivo está vacío o no tiene cabecera.")

    nombres = [celda.strip().upper() for celda in cabecera]
    if len(nombres) == 1 and SEPARADOR not in cabecera[0]:
        # Una sola columna suele indicar que el separador no es '|'.
        posibles = [s for s in (";", ",", "\t") if s in cabecera[0]]
        if posibles:
            raise ArchivoInvalidoError(f"El separador debe ser '{SEPARADOR}' (se detectó '{posibles[0]}').")

    faltantes = [c for c in COLUMNAS if c not in nombres]
    if faltantes:
        raise ArchivoInvalidoError(f"Faltan columnas en la cabecera: {', '.join(faltantes)}.")

    duplicadas = sorted({n for n in nombres if nombres.count(n) > 1})
    if duplicadas:
        raise ArchivoInvalidoError(f"Columnas repetidas en la cabecera: {', '.join(duplicadas)}.")

    return {columna: nombres.index(columna) for columna in COLUMNAS}


def _convertir_fila(fila: list[str], posiciones: dict[str, int], columnas_esperadas: int) -> AlarmaCSV:
    if len(fila) != columnas_esperadas:
        raise ValueError(f"se esperaban {columnas_esperadas} columnas y llegaron {len(fila)}")

    if any(_CARACTERES_DE_CONTROL.search(celda) for celda in fila):
        raise ValueError("la fila contiene caracteres de control (p. ej. NUL o tabulaciones)")

    valor = {columna: fila[i] for columna, i in posiciones.items()}

    id_alarma = _entero(valor["ID_ALARMA"], "ID_ALARMA", 1, ID_MAXIMO)

    try:
        fecha_creacion = parsear_fecha_oracle(valor["FECHA_CREACION"])
    except ValueError as error:
        raise ValueError(f"FECHA_CREACION inválida: {error}") from None

    notificada = valor["NOTIFICADA"].strip().upper()
    if notificada not in VALORES_NOTIFICADA:
        raise ValueError(f"NOTIFICADA debe ser 'S' o 'N' (valor: '{valor['NOTIFICADA']}')")

    return AlarmaCSV(
        id_alarma=id_alarma,
        tecnologia_2g=_entero(valor["2G"], "2G", VALOR_TECNOLOGIA_MIN, VALOR_TECNOLOGIA_MAX),
        tecnologia_3g=_entero(valor["3G"], "3G", VALOR_TECNOLOGIA_MIN, VALOR_TECNOLOGIA_MAX),
        tecnologia_4g=_entero(valor["4G"], "4G", VALOR_TECNOLOGIA_MIN, VALOR_TECNOLOGIA_MAX),
        fecha_creacion=fecha_creacion,
        municipio=_texto_obligatorio(valor["MUNICIPIO"], "MUNICIPIO"),
        departamento=_texto_obligatorio(valor["DEPARTAMENTO"], "DEPARTAMENTO"),
        notificada=notificada,
    )


def parsear_csv(contenido: bytes) -> ResultadoParseo:
    """Lee y valida el CSV completo. No toca la base de datos."""
    texto = decodificar(contenido)
    # Mismos cortes de línea que cuenta el lector CSV (splitlines() también corta en  , \x1c…).
    lineas_texto = re.split(r"\r\n|\r|\n", texto)
    lector = csv.reader(io.StringIO(texto, newline=""), delimiter=SEPARADOR, quotechar='"')

    try:
        cabecera = next(lector, None)
    except csv.Error as error:
        raise ArchivoInvalidoError(f"No se pudo leer la cabecera: {error}") from None
    posiciones = _validar_cabecera(cabecera)
    columnas_esperadas = len(cabecera)

    resultado = ResultadoParseo()
    lineas_por_id: dict[int, int] = {}

    linea_final = lector.line_num  # última línea física leída
    while True:
        linea = linea_final + 1  # primera línea física de la fila que se va a leer
        try:
            fila = next(lector)
        except StopIteration:
            break
        except csv.Error as error:
            linea_final = lector.line_num
            resultado.errores.append(ErrorFila(linea, f"fila mal formada: {error}"))
            continue
        linea_final = lector.line_num

        if not any(celda.strip() for celda in fila):
            continue  # línea en blanco

        # Una comilla sin cerrar hace que el lector absorba las líneas siguientes en un solo campo
        # (incluso hasta el final del archivo). Cada línea absorbida cuenta como rechazada.
        if linea_final > linea:
            resultado.errores.append(
                ErrorFila(linea, f"comilla sin cerrar o salto de línea dentro de un campo (líneas {linea} a {linea_final})")
            )
            resultado.errores.extend(
                ErrorFila(n, f"descartada: absorbida por la comilla sin cerrar de la línea {linea}")
                for n in range(linea + 1, linea_final + 1)
                if lineas_texto[n - 1].strip()
            )
            continue

        try:
            registro = _convertir_fila(fila, posiciones, columnas_esperadas)
        except ValueError as error:
            resultado.errores.append(ErrorFila(linea, str(error)))
            continue

        if registro.id_alarma in lineas_por_id:
            resultado.errores.append(
                ErrorFila(linea, f"ID_ALARMA {registro.id_alarma} repetido (ya aparece en la línea {lineas_por_id[registro.id_alarma]})")
            )
            continue

        lineas_por_id[registro.id_alarma] = linea
        resultado.registros.append(registro)

    return resultado


# --------------------------------------------------------------------------- #
# Persistencia
# --------------------------------------------------------------------------- #


def _ids_existentes(sesion: Session, ids: list[int]) -> set[int]:
    existentes: set[int] = set()
    for inicio in range(0, len(ids), _LOTE_CONSULTA):
        lote = ids[inicio : inicio + _LOTE_CONSULTA]
        existentes.update(sesion.scalars(select(Alarma.id_alarma).where(Alarma.id_alarma.in_(lote))))
    return existentes


def guardar_alarmas(sesion: Session, registros: list[AlarmaCSV]) -> tuple[int, int]:
    """Inserta o actualiza por ID_ALARMA. Devuelve (insertadas, actualizadas).

    La escritura es un upsert atómico (`INSERT ... ON CONFLICT DO UPDATE`), así dos importaciones
    simultáneas con los mismos IDs no chocan. Los contadores salen de una consulta previa: si hay
    importaciones simultáneas pueden ser aproximados, pero los datos quedan siempre bien guardados.
    """
    if not registros:
        return 0, 0

    existentes = _ids_existentes(sesion, [r.id_alarma for r in registros])
    insert = _INSERT_POR_MOTOR[sesion.get_bind().dialect.name]

    for inicio in range(0, len(registros), _LOTE_ESCRITURA):
        filas = [vars(r) for r in registros[inicio : inicio + _LOTE_ESCRITURA]]
        sentencia = insert(Alarma).values(filas)
        sentencia = sentencia.on_conflict_do_update(
            index_elements=[Alarma.id_alarma],
            set_={campo: sentencia.excluded[campo] for campo in filas[0] if campo != "id_alarma"},
        )
        sesion.execute(sentencia)

    sesion.commit()
    actualizadas = len(existentes)
    return len(registros) - actualizadas, actualizadas


def importar_csv(sesion: Session, contenido: bytes) -> ResultadoImportacion:
    """Parsea, valida y guarda. Lanza `ArchivoInvalidoError` si el archivo no es procesable."""
    parseo = parsear_csv(contenido)
    insertadas, actualizadas = guardar_alarmas(sesion, parseo.registros)
    return ResultadoImportacion(
        insertadas=insertadas,
        actualizadas=actualizadas,
        rechazadas=len(parseo.errores),
        errores=parseo.errores,
    )
