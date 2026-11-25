import { ETIQUETA_NIVEL, fechaLocal, partesFechaLocal } from './formato'
import type { Alarma } from './types'

export interface Columna {
  titulo: string
  /** Texto que se muestra en la tabla. */
  valor: (a: Alarma) => string | number
  /** Valor para Excel cuando conviene un tipo nativo (p. ej. fecha). Por defecto, `valor`. */
  excel?: (a: Alarma) => string | number | Date
  formatoExcel?: string
  anchoExcel: number
  numerica?: boolean
}

/**
 * Columnas visibles de la tabla. La exportación a Excel usa esta misma lista,
 * así lo exportado coincide columna a columna con lo que se ve.
 */
export const COLUMNAS: Columna[] = [
  { titulo: 'Nivel', valor: (a) => ETIQUETA_NIVEL[a.nivel], anchoExcel: 11 },
  { titulo: 'ID alarma', valor: (a) => a.id_alarma, anchoExcel: 12, numerica: true },
  { titulo: '2G', valor: (a) => a.tecnologia_2g, anchoExcel: 7, numerica: true },
  { titulo: '3G', valor: (a) => a.tecnologia_3g, anchoExcel: 7, numerica: true },
  { titulo: '4G', valor: (a) => a.tecnologia_4g, anchoExcel: 7, numerica: true },
  {
    titulo: 'Fecha de creación',
    valor: (a) => fechaLocal(a.fecha_creacion),
    // Excel no maneja zonas horarias: se guarda la hora local como si fuera UTC
    // para que la celda muestre exactamente la misma hora que la tabla.
    excel: (a) => {
      const [anio, mes, dia, hora, minuto, segundo] = partesFechaLocal(a.fecha_creacion)
      return new Date(Date.UTC(anio, mes - 1, dia, hora, minuto, segundo))
    },
    formatoExcel: 'yyyy-mm-dd hh:mm:ss',
    anchoExcel: 20,
  },
  { titulo: 'Duración', valor: (a) => a.duracion_texto, anchoExcel: 13 },
  { titulo: 'Municipio', valor: (a) => a.municipio, anchoExcel: 26 },
  { titulo: 'Departamento', valor: (a) => a.departamento, anchoExcel: 22 },
  { titulo: 'Notificada', valor: (a) => a.notificada, anchoExcel: 11 },
]
