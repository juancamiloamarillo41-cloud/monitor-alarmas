/** Tipos del contrato de la API (las respuestas del backend). */

export type NivelAlerta = 'NORMAL' | 'WARN' | 'CRITICO'

export type NivelFiltro = 'TODOS' | NivelAlerta

export interface Alarma {
  id_alarma: number
  tecnologia_2g: number
  tecnologia_3g: number
  tecnologia_4g: number
  /** ISO 8601 con zona horaria, p. ej. "2026-10-10T18:37:53-05:00". */
  fecha_creacion: string
  municipio: string
  departamento: string
  notificada: string
  duracion_segundos: number
  duracion_texto: string
  nivel: NivelAlerta
}

export interface ConteoNiveles {
  todos: number
  normal: number
  warn: number
  critico: number
}

export interface ListaAlarmas {
  consultado_en: string
  nivel: NivelFiltro
  total: number
  conteo: ConteoNiveles
  items: Alarma[]
}

export interface ErrorFila {
  linea: number
  motivo: string
}

export interface ResultadoImportacion {
  nombre_archivo: string
  insertadas: number
  actualizadas: number
  rechazadas: number
  errores: ErrorFila[]
  errores_omitidos: number
}

export interface ConteoHora {
  /** "HH:00" */
  hora: string
  cantidad: number
}

export interface ResumenDia {
  /** "YYYY-MM-DD" */
  fecha: string
  total: number
  por_hora: ConteoHora[]
}
