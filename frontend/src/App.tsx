import { useState } from 'react'
import { FiltrosNivel } from './components/FiltrosNivel'
import { ImportarArchivo } from './components/ImportarArchivo'
import { ModalResumen } from './components/ModalResumen'
import { BadgeNivel, TablaAlarmas } from './components/TablaAlarmas'
import { exportarExcel } from './exportarExcel'
import { ETIQUETA_FILTRO, formatearNumero, horaLocal } from './formato'
import { useAlarmas } from './hooks/useAlarmas'
import type { NivelFiltro } from './types'

function App() {
  const [nivel, setNivel] = useState<NivelFiltro>('TODOS')
  const [resumenAbierto, setResumenAbierto] = useState(false)
  const [exportando, setExportando] = useState(false)
  const [errorExportar, setErrorExportar] = useState<string | null>(null)
  const { datos, cargando, error, recargar } = useAlarmas(nivel)

  // Solo se muestran (y exportan) datos del filtro seleccionado. Si la consulta del filtro
  // nuevo falla, no se dejan en pantalla las filas del filtro anterior.
  const vigentes = datos?.nivel === nivel ? datos : null
  const filas = vigentes?.items ?? []

  async function exportar() {
    if (!vigentes) return
    setExportando(true)
    setErrorExportar(null)
    try {
      await exportarExcel(vigentes)
    } catch (e) {
      setErrorExportar(e instanceof Error ? e.message : 'No se pudo generar el archivo de Excel.')
    } finally {
      setExportando(false)
    }
  }

  return (
    <>
      <header className="cabecera">
        <div className="contenedor cabecera__contenido">
          <h1>Monitor de Alarmas</h1>
          <button type="button" className="boton boton--primario" onClick={() => setResumenAbierto(true)}>
            Resumen del día
          </button>
        </div>
      </header>

      <main className="contenedor">
        <ImportarArchivo onCambioDatos={recargar} hayDatos={(datos?.conteo.todos ?? 0) > 0} />

        <section className="panel" aria-labelledby="titulo-alarmas">
          <div className="panel__cabecera">
            <h2 id="titulo-alarmas">Alarmas</h2>
            <div className="acciones">
              {vigentes && (
                <span className="ayuda" title="Los datos se actualizan automáticamente cada minuto">
                  Actualizado a las {horaLocal(vigentes.consultado_en)}
                </span>
              )}
              <button type="button" className="boton" onClick={recargar} disabled={cargando}>
                {cargando ? 'Actualizando…' : 'Actualizar'}
              </button>
              <button
                type="button"
                className="boton"
                onClick={exportar}
                disabled={!vigentes || filas.length === 0 || cargando || exportando}
              >
                {exportando ? 'Generando…' : 'Exportar a Excel'}
              </button>
            </div>
          </div>

          <FiltrosNivel seleccionado={nivel} conteo={datos?.conteo} onCambiar={setNivel} />

          <div className="leyenda" aria-label="Leyenda de niveles">
            <span>
              <BadgeNivel nivel="CRITICO" /> activa más de 24 h
            </span>
            <span>
              <BadgeNivel nivel="WARN" /> activa más de 1 h y hasta 24 h
            </span>
            <span>
              <BadgeNivel nivel="NORMAL" /> no cumple las condiciones o lleva 1 h o menos
            </span>
          </div>

          {error && <p className="mensaje mensaje--error">{error}</p>}
          {errorExportar && <p className="mensaje mensaje--error">{errorExportar}</p>}

          {vigentes && (
            <p className="ayuda" aria-live="polite">
              Mostrando {formatearNumero(vigentes.total)} de {formatearNumero(vigentes.conteo.todos)} alarmas · Filtro:{' '}
              {ETIQUETA_FILTRO[vigentes.nivel]}
            </p>
          )}

          <TablaAlarmas alarmas={filas} cargando={cargando} />
        </section>
      </main>

      {resumenAbierto && <ModalResumen onCerrar={() => setResumenAbierto(false)} />}
    </>
  )
}

export default App
