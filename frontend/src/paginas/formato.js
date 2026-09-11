/** Formatos de campo: cifras con coma decimal y edades en años y meses. */

export function edad(fechaNacimiento, hoy = new Date()) {
  if (!fechaNacimiento) return 'edad sin registrar'
  const dias = Math.floor((hoy - new Date(fechaNacimiento)) / 86400000)
  if (dias < 0) return 'edad sin registrar'
  const años = Math.floor(dias / 365)
  const meses = Math.floor((dias % 365) / 30)
  if (años > 0) return `${años} a ${meses} m`
  return meses > 0 ? `${meses} meses` : `${dias} días`
}

export function kilos(valor) {
  if (valor === null || valor === undefined) return null
  return `${Number(valor).toFixed(1).replace('.', ',')} kg`
}

const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

/** «07 abr 2021». Corto, sin preposiciones, para que quepa en una celda. */
export function fechaCorta(valor) {
  if (!valor) return null
  const fecha = new Date(`${valor}T00:00:00`)
  if (Number.isNaN(fecha.getTime())) return null
  return `${String(fecha.getDate()).padStart(2, '0')} ${MESES[fecha.getMonth()]} ${fecha.getFullYear()}`
}

export const ESTADOS = {
  activo: { texto: 'Activo', tono: 'ok' },
  en_engorde: { texto: 'En engorde', tono: 'neutro' },
  vendido: { texto: 'Vendido', tono: 'neutro' },
  muerto: { texto: 'Muerto', tono: 'vencido' },
  descartado: { texto: 'Descartado', tono: 'pronto' },
}

export const SEXOS = { hembra: 'Hembra', macho: 'Macho' }
