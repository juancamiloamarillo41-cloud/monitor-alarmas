import { ETIQUETA_FILTRO, formatearNumero } from '../formato'
import type { ConteoNiveles, NivelFiltro } from '../types'

const OPCIONES: { nivel: NivelFiltro; clave: keyof ConteoNiveles }[] = [
  { nivel: 'TODOS', clave: 'todos' },
  { nivel: 'WARN', clave: 'warn' },
  { nivel: 'CRITICO', clave: 'critico' },
  { nivel: 'NORMAL', clave: 'normal' },
]

interface Props {
  seleccionado: NivelFiltro
  conteo: ConteoNiveles | undefined
  onCambiar: (nivel: NivelFiltro) => void
}

export function FiltrosNivel({ seleccionado, conteo, onCambiar }: Props) {
  return (
    <div className="filtros" role="group" aria-label="Filtrar por nivel de alerta">
      {OPCIONES.map(({ nivel, clave }) => (
        <button
          key={nivel}
          type="button"
          className={`filtro filtro--${nivel.toLowerCase()}`}
          aria-pressed={seleccionado === nivel}
          onClick={() => onCambiar(nivel)}
        >
          {ETIQUETA_FILTRO[nivel]}
          <span className="filtro__conteo">{conteo ? formatearNumero(conteo[clave]) : '–'}</span>
        </button>
      ))}
    </div>
  )
}
