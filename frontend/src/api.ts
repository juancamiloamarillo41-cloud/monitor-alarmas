/** Cliente de la API REST del backend. La URL base viene de VITE_API_URL (.env). */

import type { ListaAlarmas, NivelFiltro, ResultadoImportacion, ResumenDia } from './types'

const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  readonly estado: number

  constructor(estado: number, mensaje: string) {
    super(mensaje)
    this.name = 'ApiError'
    this.estado = estado
  }
}

/** Extrae un mensaje legible del cuerpo de error de FastAPI ({ detail: string | [...] }). */
async function mensajeDeError(respuesta: Response): Promise<string> {
  try {
    const cuerpo: unknown = await respuesta.json()
    if (cuerpo && typeof cuerpo === 'object' && 'detail' in cuerpo) {
      const detalle = (cuerpo as { detail: unknown }).detail
      if (typeof detalle === 'string') return detalle
      if (Array.isArray(detalle)) {
        return detalle.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join('; ')
      }
    }
  } catch {
    // cuerpo vacío o no JSON
  }
  return `Error ${respuesta.status} (${respuesta.statusText || 'sin detalle'})`
}

async function solicitar<T>(ruta: string, opciones?: RequestInit): Promise<T> {
  let respuesta: Response
  try {
    respuesta = await fetch(`${API_URL}${ruta}`, opciones)
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(0, `No se pudo conectar con el backend (${API_URL}).`)
  }
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await mensajeDeError(respuesta))
  }
  if (respuesta.status === 204) return undefined as T
  return respuesta.json() as Promise<T>
}

export function obtenerSalud(): Promise<{ estado: string }> {
  return solicitar('/api/salud')
}

export function listarAlarmas(nivel: NivelFiltro, signal?: AbortSignal): Promise<ListaAlarmas> {
  return solicitar(`/api/alarmas?nivel=${encodeURIComponent(nivel)}`, { signal })
}

export function importarArchivo(archivo: File): Promise<ResultadoImportacion> {
  const datos = new FormData()
  datos.append('archivo', archivo)
  return solicitar('/api/alarmas/importar', { method: 'POST', body: datos })
}

export function vaciarAlarmas(): Promise<void> {
  return solicitar('/api/alarmas', { method: 'DELETE' })
}

export function obtenerResumenDia(signal?: AbortSignal): Promise<ResumenDia> {
  return solicitar('/api/alarmas/resumen-dia', { signal })
}

export function esAborto(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}
