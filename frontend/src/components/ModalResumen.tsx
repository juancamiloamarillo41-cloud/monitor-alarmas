import { useEffect, useRef, useState } from 'react'
import { ApiError, esAborto, obtenerResumenDia } from '../api'
import { formatearNumero } from '../formato'
import type { ResumenDia } from '../types'

interface Props {
  onCerrar: () => void
}

type Estado =
  | { tipo: 'cargando' }
  | { tipo: 'ok'; resumen: ResumenDia }
  | { tipo: 'error'; mensaje: string }

/**
 * Modal del resumen del día. Se monta solo mientras está abierto, así cada
 * apertura consulta el servicio de nuevo y el resumen siempre está al día.
 */
export function ModalResumen({ onCerrar }: Props) {
  const dialogo = useRef<HTMLDialogElement>(null)
  const [estado, setEstado] = useState<Estado>({ tipo: 'cargando' })

  // <dialog> nativo en modo modal: atrapa el foco y se cierra con Esc.
  useEffect(() => {
    const d = dialogo.current
    if (d && !d.open) d.showModal()
  }, [])

  useEffect(() => {
    const control = new AbortController()
    obtenerResumenDia(control.signal)
      .then((resumen) => setEstado({ tipo: 'ok', resumen }))
      .catch((e: unknown) => {
        if (esAborto(e)) return
        const mensaje =
          e instanceof ApiError && e.estado === 404
            ? 'El servicio de resumen del día todavía no está disponible en el backend.'
            : e instanceof Error
              ? e.message
              : 'Error al obtener el resumen.'
        setEstado({ tipo: 'error', mensaje })
      })
    return () => control.abort()
  }, [])

  return (
    <dialog
      ref={dialogo}
      className="modal"
      aria-labelledby="titulo-resumen"
      onClose={onCerrar}
      onClick={(e) => {
        if (e.target === e.currentTarget) onCerrar() // clic en el fondo
      }}
    >
      <div className="modal__contenido">
        <header className="modal__cabecera">
          <h2 id="titulo-resumen">Resumen del día</h2>
          <button type="button" className="boton boton--icono" onClick={onCerrar} aria-label="Cerrar">
            ×
          </button>
        </header>

        {estado.tipo === 'cargando' && <p className="ayuda">Cargando resumen…</p>}
        {estado.tipo === 'error' && <p className="mensaje mensaje--error">{estado.mensaje}</p>}
        {estado.tipo === 'ok' && <ContenidoResumen resumen={estado.resumen} />}
      </div>
    </dialog>
  )
}

function ContenidoResumen({ resumen }: { resumen: ResumenDia }) {
  const maximo = Math.max(1, ...resumen.por_hora.map((h) => h.cantidad))

  return (
    <>
      <p className="resumen__total">
        <strong>{formatearNumero(resumen.total)}</strong> alarmas creadas hoy ({resumen.fecha})
      </p>
      {resumen.total === 0 ? (
        <p className="ayuda">No se han creado alarmas hoy.</p>
      ) : (
        <ol className="horas" aria-label="Alarmas creadas por hora">
          {resumen.por_hora.map(({ hora, cantidad }) => (
            <li key={hora} className={`hora${cantidad === 0 ? ' hora--vacia' : ''}`}>
              <span className="hora__etiqueta">{hora}</span>
              <span className="hora__barra" aria-hidden="true">
                <span style={{ width: `${(cantidad / maximo) * 100}%` }} />
              </span>
              <span className="hora__cantidad">{formatearNumero(cantidad)}</span>
            </li>
          ))}
        </ol>
      )}
    </>
  )
}
