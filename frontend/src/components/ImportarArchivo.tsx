import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { importarArchivo, vaciarAlarmas } from '../api'
import { formatearNumero } from '../formato'
import type { ResultadoImportacion } from '../types'

interface Props {
  /** Se llama después de importar o vaciar, para recargar la tabla. */
  onCambioDatos: () => void
  hayDatos: boolean
}

export function ImportarArchivo({ onCambioDatos, hayDatos }: Props) {
  const entrada = useRef<HTMLInputElement>(null)
  const [archivo, setArchivo] = useState<File | null>(null)
  const [enProceso, setEnProceso] = useState(false)
  const [resultado, setResultado] = useState<ResultadoImportacion | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function importar(evento: FormEvent) {
    evento.preventDefault()
    if (!archivo) return
    setEnProceso(true)
    setError(null)
    setResultado(null)
    try {
      setResultado(await importarArchivo(archivo))
      setArchivo(null)
      if (entrada.current) entrada.current.value = ''
      onCambioDatos()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error inesperado al importar.')
    } finally {
      setEnProceso(false)
    }
  }

  async function vaciar() {
    if (!window.confirm('¿Eliminar todas las alarmas importadas? Esta acción no se puede deshacer.')) return
    setEnProceso(true)
    setError(null)
    setResultado(null)
    try {
      await vaciarAlarmas()
      onCambioDatos()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error inesperado al vaciar.')
    } finally {
      setEnProceso(false)
    }
  }

  return (
    <section className="panel" aria-labelledby="titulo-importar">
      <h2 id="titulo-importar">Importar alarmas</h2>
      <form className="importar" onSubmit={importar}>
        <label className="importar__archivo">
          <span className="visualmente-oculto">Archivo CSV separado por |</span>
          <input
            ref={entrada}
            type="file"
            accept=".csv,text/csv"
            disabled={enProceso}
            onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
          />
        </label>
        <button type="submit" className="boton boton--primario" disabled={!archivo || enProceso}>
          {enProceso ? 'Procesando…' : 'Importar'}
        </button>
        <button type="button" className="boton boton--peligro" disabled={!hayDatos || enProceso} onClick={vaciar}>
          Vaciar datos
        </button>
      </form>
      <p className="ayuda">Formato: CSV separado por “|” con las columnas ID_ALARMA, 2G, 3G, 4G, FECHA_CREACION, MUNICIPIO, DEPARTAMENTO y NOTIFICADA.</p>

      <div aria-live="polite">
        {error && <p className="mensaje mensaje--error">{error}</p>}
        {resultado && <ResumenImportacion resultado={resultado} />}
      </div>
    </section>
  )
}

function ResumenImportacion({ resultado }: { resultado: ResultadoImportacion }) {
  const { insertadas, actualizadas, rechazadas, errores, errores_omitidos } = resultado
  return (
    <div className={`mensaje ${rechazadas ? 'mensaje--aviso' : 'mensaje--ok'}`}>
      <p>
        <strong>{resultado.nombre_archivo}</strong>: {formatearNumero(insertadas)} insertadas,{' '}
        {formatearNumero(actualizadas)} actualizadas, {formatearNumero(rechazadas)} rechazadas.
      </p>
      {errores.length > 0 && (
        <details>
          <summary>Ver filas rechazadas</summary>
          <ul className="errores-fila">
            {errores.map((e) => (
              <li key={e.linea}>
                Línea {e.linea}: {e.motivo}
              </li>
            ))}
          </ul>
          {errores_omitidos > 0 && <p>… y {formatearNumero(errores_omitidos)} filas rechazadas más.</p>}
        </details>
      )}
    </div>
  )
}
