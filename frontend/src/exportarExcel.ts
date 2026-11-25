import { COLUMNAS } from './columnas'
import { ETIQUETA_FILTRO, fechaLocal } from './formato'
import type { ListaAlarmas, NivelAlerta } from './types'

const RELLENO_NIVEL: Record<NivelAlerta, string | null> = {
  CRITICO: 'FFFDE3E1',
  WARN: 'FFFFF1D6',
  NORMAL: null,
}

/**
 * Genera y descarga un .xlsx con exactamente las filas y columnas que muestra la tabla
 * (mismo filtro, mismo orden y la misma duración calculada en `consultado_en`).
 */
export async function exportarExcel(datos: ListaAlarmas): Promise<void> {
  // Carga diferida: exceljs es pesado y solo se necesita al exportar.
  const { Workbook } = await import('exceljs')
  const libro = new Workbook()
  libro.creator = 'Monitor de Alarmas'
  libro.created = new Date()

  const hoja = libro.addWorksheet('Alarmas', { views: [{ state: 'frozen', ySplit: 1 }] })
  hoja.columns = COLUMNAS.map((c) => ({
    header: c.titulo,
    width: c.anchoExcel,
    style: c.formatoExcel ? { numFmt: c.formatoExcel } : {},
  }))

  const encabezado = hoja.getRow(1)
  encabezado.font = { bold: true, color: { argb: 'FFFFFFFF' } }
  encabezado.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF1D2330' } }

  for (const alarma of datos.items) {
    const fila = hoja.addRow(COLUMNAS.map((c) => (c.excel ?? c.valor)(alarma)))
    const relleno = RELLENO_NIVEL[alarma.nivel]
    if (relleno) {
      fila.eachCell({ includeEmpty: true }, (celda) => {
        celda.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: relleno } }
      })
    }
  }

  hoja.autoFilter = { from: { row: 1, column: 1 }, to: { row: 1, column: COLUMNAS.length } }

  const info = libro.addWorksheet('Información')
  info.columns = [{ width: 22 }, { width: 30 }]
  info.addRows([
    ['Filtro aplicado', ETIQUETA_FILTRO[datos.nivel]],
    ['Consultado en', fechaLocal(datos.consultado_en)],
    ['Registros exportados', datos.items.length],
  ])
  info.getColumn(1).font = { bold: true }

  const contenido = await libro.xlsx.writeBuffer()
  const blob = new Blob([contenido], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
  descargar(blob, nombreArchivo(datos))
}

function nombreArchivo(datos: ListaAlarmas): string {
  // "2026-11-24T18:15:26..." -> "20261124-1815"
  const marca = datos.consultado_en.slice(0, 16).replace(/[-:]/g, '').replace('T', '-')
  return `alarmas_${datos.nivel.toLowerCase()}_${marca}.xlsx`
}

function descargar(blob: Blob, nombre: string): void {
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombre
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  URL.revokeObjectURL(url)
}
