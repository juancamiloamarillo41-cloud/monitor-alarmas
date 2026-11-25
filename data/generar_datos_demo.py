"""Genera un CSV de demostración con fechas relativas al momento actual.

La muestra entregada con la prueba tiene fechas de sep–nov 2026, así que con el
paso del tiempo todas sus alarmas quedan en CRÍTICO o NORMAL y no hay alarmas
de "hoy" para el resumen. Este script crea un archivo con el mismo formato
(separado por '|', fechas Oracle) que incluye:

  1. Casos guiados que cumplen las condiciones base con distintas antigüedades
     (NORMAL <= 1 h, WARN 1–24 h, CRÍTICO > 24 h) y distintas combinaciones de
     tecnologías no disponibles (-100).
  2. Casos de control que NO cumplen las condiciones base (siempre NORMAL).
  3. Alarmas repartidas en las horas transcurridas del día de hoy, para el
     resumen del día.

Al final imprime cuántas alarmas de cada nivel se esperan y la distribución por
hora de hoy, para comparar con lo que muestra la aplicación.

No depende del backend: solo usa la biblioteca estándar de Python.

Uso:
    python data/generar_datos_demo.py
    python data/generar_datos_demo.py --salida data/datos_demo.csv --semilla 7 --por-hora 6
"""

import argparse
import random
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Colombia no tiene horario de verano: America/Bogota es siempre UTC-5.
ZONA_BOGOTA = timezone(timedelta(hours=-5), "America/Bogota")

CABECERA = '"ID_ALARMA"|"2G"|"3G"|"4G"|"FECHA_CREACION"|"MUNICIPIO"|"DEPARTAMENTO"|"NOTIFICADA"'
MESES = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")

ID_INICIAL = 9_000_001  # fuera del rango de la muestra (46xxxxx) para no pisar sus registros

UBICACIONES = (
    ("Bogotá", "Cundinamarca"),
    ("Medellín", "Antioquia"),
    ("Cali", "Valle del Cauca"),
    ("Barranquilla", "Atlántico"),
    ("Cartagena", "Bolívar"),
    ("Bucaramanga", "Santander"),
    ("Cúcuta", "N de Santander"),
    ("Pereira", "Risaralda"),
    ("Manizales", "Caldas"),
    ("Ibagué", "Tolima"),
    ("Villavicencio", "Meta"),
    ("Pasto", "Nariño"),
    ("Neiva", "Huila"),
    ("Popayán", "Cauca"),
    ("Quibdó", "Chocó"),
    ("Inírida", "Guainía"),
)

AL_LIMITE = (100, 100, 100)
NO_DISPONIBLE = -100

# Casos guiados: (tecnologías, antigüedad). Todos con NOTIFICADA = 'N'.
CASOS_BASE: tuple[tuple[tuple[int, int, int], timedelta], ...] = (
    (AL_LIMITE, timedelta(minutes=10)),  # NORMAL: cumple base pero lleva <= 1 h
    (AL_LIMITE, timedelta(minutes=45)),  # NORMAL
    ((NO_DISPONIBLE, 100, 100), timedelta(hours=1, minutes=5)),  # WARN (justo pasada 1 h)
    (AL_LIMITE, timedelta(hours=2)),  # WARN
    ((100, NO_DISPONIBLE, 100), timedelta(hours=6)),  # WARN
    ((NO_DISPONIBLE, NO_DISPONIBLE, 100), timedelta(hours=12)),  # WARN
    (AL_LIMITE, timedelta(hours=20)),  # WARN
    (AL_LIMITE, timedelta(hours=23, minutes=30)),  # WARN (cerca de las 24 h)
    (AL_LIMITE, timedelta(hours=25)),  # CRÍTICO (justo pasadas 24 h)
    ((NO_DISPONIBLE, 100, 100), timedelta(days=2)),  # CRÍTICO
    ((100, 100, NO_DISPONIBLE), timedelta(days=5)),  # CRÍTICO
)

# Casos de control: no cumplen las condiciones base -> siempre NORMAL.
CASOS_CONTROL: tuple[tuple[tuple[int, int, int], timedelta, str], ...] = (
    ((0, 0, 100), timedelta(hours=3), "N"),  # 0 está disponible y no es 100
    ((100, 100, 99), timedelta(hours=8), "N"),  # una disponible no está al límite
    (AL_LIMITE, timedelta(hours=4), "S"),  # ya notificada
    (AL_LIMITE, timedelta(days=2), "S"),  # ya notificada
    ((NO_DISPONIBLE, NO_DISPONIBLE, NO_DISPONIBLE), timedelta(hours=5), "N"),  # ninguna disponible
)


@dataclass(frozen=True)
class AlarmaDemo:
    id_alarma: int
    tecnologias: tuple[int, int, int]
    fecha_creacion: datetime  # hora local de Bogotá, sin zona
    municipio: str
    departamento: str
    notificada: str

    def a_linea(self) -> str:
        t2g, t3g, t4g = self.tecnologias
        return (
            f"{self.id_alarma}|{t2g}|{t3g}|{t4g}|{formatear_fecha_oracle(self.fecha_creacion)}"
            f'|"{self.municipio}"|"{self.departamento}"|"{self.notificada}"'
        )


def formatear_fecha_oracle(fecha: datetime) -> str:
    """datetime -> '09-OCT-26 10.12.56.000000000 PM' (mismo formato de la muestra)."""
    hora_12 = fecha.hour % 12 or 12
    meridiano = "PM" if fecha.hour >= 12 else "AM"
    return (
        f"{fecha.day:02d}-{MESES[fecha.month - 1]}-{fecha.year % 100:02d} "
        f"{hora_12:02d}.{fecha.minute:02d}.{fecha.second:02d}.000000000 {meridiano}"
    )


def nivel_esperado(alarma: AlarmaDemo, ahora: datetime) -> str:
    """Nivel esperado según la regla documentada (sirve para verificar la aplicación)."""
    disponibles = [v for v in alarma.tecnologias if v >= 0]
    cumple_base = bool(disponibles) and all(v == 100 for v in disponibles) and alarma.notificada == "N"
    if not cumple_base:
        return "NORMAL"
    duracion = ahora - alarma.fecha_creacion
    if duracion > timedelta(hours=24):
        return "CRITICO"
    if duracion > timedelta(hours=1):
        return "WARN"
    return "NORMAL"


def tecnologias_aleatorias(azar: random.Random) -> tuple[int, int, int]:
    """Valores parecidos a la muestra: muchos 0, algunos -100 y ocasionalmente 100."""
    opciones = [0, 0, 0, 0, 3, 10, 17, 25, 33, 50, 67, 88, 100, NO_DISPONIBLE]
    return tuple(azar.choice(opciones) for _ in range(3))  # type: ignore[return-value]


def generar(ahora: datetime, semilla: int = 2026, por_hora: int = 5) -> list[AlarmaDemo]:
    """Genera las alarmas de demostración. `ahora` es la hora local de Bogotá sin zona."""
    azar = random.Random(semilla)
    ahora = ahora.replace(microsecond=0)
    alarmas: list[AlarmaDemo] = []

    def agregar(tecnologias: tuple[int, int, int], fecha: datetime, notificada: str = "N") -> None:
        municipio, departamento = azar.choice(UBICACIONES)
        alarmas.append(
            AlarmaDemo(ID_INICIAL + len(alarmas), tecnologias, fecha, municipio, departamento, notificada)
        )

    for tecnologias, antiguedad in CASOS_BASE:
        agregar(tecnologias, ahora - antiguedad)

    for tecnologias, antiguedad, notificada in CASOS_CONTROL:
        agregar(tecnologias, ahora - antiguedad, notificada)

    # Alarmas de hoy, hora por hora hasta la hora actual (para el resumen del día).
    inicio_dia = ahora.replace(hour=0, minute=0, second=0)
    for hora in range(ahora.hour + 1):
        inicio_franja = inicio_dia + timedelta(hours=hora)
        segundos_disponibles = int(min(timedelta(hours=1), ahora - inicio_franja).total_seconds())
        if segundos_disponibles <= 0:
            continue
        for _ in range(azar.randint(0, por_hora * 2)):
            fecha = inicio_franja + timedelta(seconds=azar.randrange(segundos_disponibles))
            # Uno de cada cinco cumple las condiciones base, para que haya WARN entre las de hoy.
            tecnologias = AL_LIMITE if azar.random() < 0.2 else tecnologias_aleatorias(azar)
            agregar(tecnologias, fecha, "S" if azar.random() < 0.05 else "N")

    return alarmas


def escribir_csv(alarmas: list[AlarmaDemo], ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    lineas = [CABECERA, *(a.a_linea() for a in alarmas)]
    ruta.write_text("\r\n".join(lineas), encoding="utf-8", newline="")


def imprimir_resumen(alarmas: list[AlarmaDemo], ahora: datetime, ruta: Path) -> None:
    niveles = Counter(nivel_esperado(a, ahora) for a in alarmas)
    hoy = [a for a in alarmas if a.fecha_creacion.date() == ahora.date()]
    por_hora = Counter(a.fecha_creacion.hour for a in hoy)

    print(f"Archivo generado: {ruta}")
    print(f"Generado a las {ahora:%Y-%m-%d %H:%M:%S} (America/Bogota) con {len(alarmas)} alarmas.\n")
    print("Niveles esperados en este momento:")
    for nivel in ("CRITICO", "WARN", "NORMAL"):
        print(f"  {nivel:<8} {niveles[nivel]:>4}")
    print("\nAlarmas creadas hoy por hora (para validar el resumen del día):")
    for hora in range(24):
        print(f"  {hora:02d}:00 {por_hora[hora]:>4}")
    print(f"  Total   {len(hoy):>4}")
    print(
        "\nNota: los niveles dependen del tiempo. Importa el archivo poco después de generarlo;"
        "\nlas alarmas de menos de 1 h pasarán a WARN con el paso de los minutos."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--salida",
        type=Path,
        default=Path(__file__).resolve().parent / "datos_demo.csv",
        help="Ruta del CSV a generar (por defecto data/datos_demo.csv).",
    )
    parser.add_argument("--semilla", type=int, default=2026, help="Semilla para obtener siempre los mismos valores.")
    parser.add_argument("--por-hora", type=int, default=5, help="Promedio de alarmas por hora del día de hoy.")
    args = parser.parse_args()

    ahora = datetime.now(ZONA_BOGOTA).replace(tzinfo=None, microsecond=0)
    alarmas = generar(ahora, semilla=args.semilla, por_hora=args.por_hora)
    escribir_csv(alarmas, args.salida)
    imprimir_resumen(alarmas, ahora, args.salida)


if __name__ == "__main__":
    main()
