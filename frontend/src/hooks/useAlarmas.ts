import { useCallback, useEffect, useState } from 'react'
import { esAborto, listarAlarmas } from '../api'
import type { ListaAlarmas, NivelFiltro } from '../types'

/** Cada minuto se vuelve a consultar para que la duración y el nivel avancen. */
export const INTERVALO_REFRESCO_MS = 60_000

/**
 * Carga las alarmas del nivel indicado y las refresca periódicamente.
 * La clasificación siempre viene del backend; aquí no se recalcula nada.
 */
export function useAlarmas(nivel: NivelFiltro) {
  const [datos, setDatos] = useState<ListaAlarmas | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [version, setVersion] = useState(0)

  // Cada consulta se identifica por filtro + versión; se está cargando mientras
  // la última consulta pedida no haya terminado.
  const consulta = `${nivel}#${version}`
  const [consultaTerminada, setConsultaTerminada] = useState<string | null>(null)
  const cargando = consultaTerminada !== consulta

  const recargar = useCallback(() => setVersion((v) => v + 1), [])

  useEffect(() => {
    // Cancela la petición anterior si cambia el filtro antes de que responda.
    const control = new AbortController()
    listarAlarmas(nivel, control.signal)
      .then((respuesta) => {
        setDatos(respuesta)
        setError(null)
      })
      .catch((e: unknown) => {
        if (!esAborto(e)) setError(e instanceof Error ? e.message : 'Error al cargar las alarmas.')
      })
      .finally(() => {
        if (!control.signal.aborted) setConsultaTerminada(consulta)
      })
    return () => control.abort()
  }, [nivel, consulta])

  useEffect(() => {
    const id = window.setInterval(recargar, INTERVALO_REFRESCO_MS)
    return () => window.clearInterval(id)
  }, [recargar])

  return { datos, cargando, error, recargar }
}
