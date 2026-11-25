import type { NivelAlerta, NivelFiltro } from './types'

export const ETIQUETA_NIVEL: Record<NivelAlerta, string> = {
  NORMAL: 'Normal',
  WARN: 'WARN',
  CRITICO: 'CRÍTICO',
}

export const ETIQUETA_FILTRO: Record<NivelFiltro, string> = {
  TODOS: 'Todos',
  WARN: 'WARN',
  CRITICO: 'CRÍTICO',
  NORMAL: 'Normales',
}

/**
 * "2026-10-10T18:37:53-05:00" -> "2026-10-10 18:37:53".
 * Se toma la hora local tal como la envía el backend (America/Bogota),
 * sin convertirla a la zona horaria del navegador.
 */
export function fechaLocal(iso: string): string {
  return iso.slice(0, 19).replace('T', ' ')
}

/** Partes numéricas de la hora local de un ISO 8601: [año, mes(1-12), día, hora, minuto, segundo]. */
export function partesFechaLocal(iso: string): number[] {
  return fechaLocal(iso).split(/[- :]/).map(Number)
}

export function horaLocal(iso: string): string {
  return fechaLocal(iso).slice(11)
}

export function formatearNumero(valor: number): string {
  return valor.toLocaleString('es-CO')
}
