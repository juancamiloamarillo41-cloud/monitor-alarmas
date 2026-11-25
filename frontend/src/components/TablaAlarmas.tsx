import { COLUMNAS } from '../columnas'
import { ETIQUETA_NIVEL, fechaLocal } from '../formato'
import type { Alarma, NivelAlerta } from '../types'

const NO_DISPONIBLE = -100

interface Props {
  alarmas: Alarma[]
  cargando: boolean
}

export function TablaAlarmas({ alarmas, cargando }: Props) {
  return (
    <div className="tabla-contenedor" aria-busy={cargando}>
      <table className="tabla">
        <thead>
          <tr>
            {COLUMNAS.map((c) => (
              <th key={c.titulo} scope="col" className={c.numerica ? 'num' : undefined}>
                {c.titulo}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {alarmas.length === 0 ? (
            <tr>
              <td colSpan={COLUMNAS.length} className="tabla__vacia">
                {cargando ? 'Cargando…' : 'No hay alarmas para mostrar.'}
              </td>
            </tr>
          ) : (
            alarmas.map((a) => (
              <tr key={a.id_alarma} className={`fila fila--${a.nivel.toLowerCase()}`}>
                <td>
                  <BadgeNivel nivel={a.nivel} />
                </td>
                <td className="num">{a.id_alarma}</td>
                <CeldaTecnologia valor={a.tecnologia_2g} />
                <CeldaTecnologia valor={a.tecnologia_3g} />
                <CeldaTecnologia valor={a.tecnologia_4g} />
                <td className="nowrap">{fechaLocal(a.fecha_creacion)}</td>
                <td className="nowrap duracion" title={`${a.duracion_segundos.toLocaleString('es-CO')} segundos`}>
                  {a.duracion_texto}
                </td>
                <td>{a.municipio}</td>
                <td>{a.departamento}</td>
                <td className="centro">{a.notificada}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}

export function BadgeNivel({ nivel }: { nivel: NivelAlerta }) {
  return <span className={`badge badge--${nivel.toLowerCase()}`}>{ETIQUETA_NIVEL[nivel]}</span>
}

function CeldaTecnologia({ valor }: { valor: number }) {
  if (valor === NO_DISPONIBLE) {
    return (
      <td className="num tecnologia--nd" title="Tecnología no disponible">
        {valor}
      </td>
    )
  }
  return <td className={`num${valor === 100 ? ' tecnologia--limite' : ''}`}>{valor}</td>
}
