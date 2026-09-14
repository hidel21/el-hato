/**
 * Derivacion de alertas en el dispositivo.
 *
 * Decision 6: lo que se puede calcular desde los datos —proxima dosis, parto
 * estimado, dias de carencia, dias de ocupacion de un potrero— se calcula
 * AQUI, no en el servidor. Tiene que funcionar sin señal, y el dispositivo ya
 * tiene los datos.
 *
 * Estas funciones son puras a proposito: hoy reciben lo que trajo la red, y en
 * la Fase 2 recibiran lo mismo leido de IndexedDB. El calculo no cambia.
 */

const DIA = 86400000

export const VENCIDA = 'vencida'
export const ESTA_SEMANA = 'esta_semana'
export const PROXIMA = 'proxima'

/** Hasta cuantos dias hacia adelante vale la pena mirar. */
const HORIZONTE_DIAS = 90

function aFecha(texto) {
  return texto ? new Date(`${texto}T00:00:00`) : null
}

function diasHasta(fecha, hoy) {
  return Math.round((fecha - hoy) / DIA)
}

function urgencia(dias) {
  if (dias < 0) return VENCIDA
  if (dias <= 7) return ESTA_SEMANA
  return PROXIMA
}

/** Clave estable de una alerta derivada: de que tabla sale y de que fila. */
export function claveDe(alerta) {
  return `${alerta.referencia_tabla}:${alerta.referencia_id}`
}

/**
 * Las que ya se marcaron atendidas o descartadas, desde cualquier dispositivo.
 * Viven en la tabla de alertas del servidor, que es lo unico que viaja.
 */
function resueltas(guardadas = []) {
  return new Set(
    guardadas
      .filter(
        (a) =>
          (a.estado === 'atendida' || a.estado === 'descartada') &&
          a.referencia_tabla &&
          a.referencia_id
      )
      .map((a) => `${a.referencia_tabla}:${a.referencia_id}`)
  )
}

function porVacunaciones(vacunaciones, hoy) {
  return vacunaciones
    .filter((v) => v.proxima_dosis_fecha)
    .map((v) => {
      const fecha = aFecha(v.proxima_dosis_fecha)
      const dias = diasHasta(fecha, hoy)
      const cuantos = v.cantidad_animales
      return {
        tipo: 'vacunacion',
        etiqueta: 'Vacuna',
        titulo:
          cuantos > 1
            ? `${cuantos} refuerzos de ${v.vacuna_nombre}`
            : `Refuerzo de ${v.vacuna_nombre}`,
        detalle: v.grupo_nombre ?? v.animal_arete ?? 'Aplicación individual',
        fecha: v.proxima_dosis_fecha,
        dias,
        urgencia: urgencia(dias),
        arete: v.animal_arete ?? 'Lote',
        animal_id: v.animal_id,
        referencia_tabla: 'vacunaciones',
        referencia_id: v.id,
      }
    })
}

function porBanos(banos, hoy) {
  return banos
    .filter((b) => b.proxima_fecha)
    .map((b) => {
      const fecha = aFecha(b.proxima_fecha)
      const dias = diasHasta(fecha, hoy)
      return {
        tipo: 'bano',
        etiqueta: 'Baño',
        titulo: `${b.producto_nombre} a ${b.cantidad_animales} ${
          b.cantidad_animales === 1 ? 'animal' : 'animales'
        }`,
        detalle: b.grupo_nombre ?? b.potrero_nombre ?? 'Aplicación individual',
        fecha: b.proxima_fecha,
        dias,
        urgencia: urgencia(dias),
        arete: 'Lote',
        animal_id: null,
        referencia_tabla: 'banos',
        referencia_id: b.id,
      }
    })
}

/**
 * Partos estimados. Manda el diagnostico de preñez sobre el servicio: si la
 * palparon, esa es la informacion buena. Un servicio con diagnostico posterior
 * ya no genera alerta propia.
 */
/**
 * Una gestacion se cierra cuando la vaca pare. Sin esto, un diagnostico viejo
 * seguiria pidiendo un parto que ya ocurrio: la alerta mas irritante posible,
 * porque el capataz sabe perfectamente que esa vaca ya pario.
 */
function cerradaPorParto(partos, animalId, desde) {
  return partos.some((parto) => parto.madre_id === animalId && parto.fecha_parto >= desde)
}

function porPartos(servicios, diagnosticos, partos, hoy) {
  const conDiagnostico = new Set(diagnosticos.map((d) => d.servicio_id).filter(Boolean))

  const desdeDiagnostico = diagnosticos
    .filter(
      (d) =>
        d.resultado === 'prenada' &&
        d.fecha_estimada_parto &&
        !cerradaPorParto(partos, d.animal_id, d.fecha_diagnostico)
    )
    .map((d) => ({
      fuente: d,
      tabla: 'diagnosticos_prenez',
      fecha: d.fecha_estimada_parto,
      arete: d.animal_arete,
      animal_id: d.animal_id,
    }))

  const desdeServicio = servicios
    .filter(
      (s) =>
        s.fecha_estimada_parto &&
        !conDiagnostico.has(s.id) &&
        !cerradaPorParto(partos, s.animal_id, s.fecha_servicio)
    )
    .map((s) => ({
      fuente: s,
      tabla: 'servicios_reproductivos',
      fecha: s.fecha_estimada_parto,
      arete: s.animal_arete,
      animal_id: s.animal_id,
      sinConfirmar: true,
    }))

  return [...desdeDiagnostico, ...desdeServicio].map((origen) => {
    const dias = diasHasta(aFecha(origen.fecha), hoy)
    return {
      tipo: 'parto',
      etiqueta: 'Parto',
      titulo: origen.sinConfirmar
        ? `${origen.arete} sin diagnóstico de preñez`
        : `Parto estimado de ${origen.arete}`,
      detalle: origen.sinConfirmar
        ? 'Servida y aún sin palpar'
        : dias < 0
          ? `Debió parir hace ${Math.abs(dias)} días`
          : `Faltan ${dias} días`,
      fecha: origen.fecha,
      dias,
      urgencia: urgencia(dias),
      arete: origen.arete,
      animal_id: origen.animal_id,
      referencia_tabla: origen.tabla,
      referencia_id: origen.fuente.id,
    }
  })
}

/** Potreros que pasaron los dias de ocupacion que aguanta el pasto. */
function porRotacion(potreros, hoy) {
  return potreros
    .filter((p) => !p.en_descanso && p.fecha_ultimo_ingreso && p.cantidad_animales > 0)
    .map((p) => {
      const ocupado = -diasHasta(aFecha(p.fecha_ultimo_ingreso), hoy)
      const restantes = p.dias_descanso_recomendado - ocupado
      return {
        tipo: 'rotacion',
        etiqueta: 'Rotar',
        titulo: `${p.nombre} lleva ${ocupado} días ocupado`,
        detalle: `Se recomienda rotar a los ${p.dias_descanso_recomendado} días`,
        fecha: null,
        dias: restantes,
        urgencia: urgencia(restantes),
        arete: 'Potrero',
        animal_id: null,
        referencia_tabla: 'potreros',
        referencia_id: p.id,
      }
    })
    .filter((alerta) => alerta.dias <= 7)
}

/**
 * Todas las alertas del hato, agrupadas por urgencia.
 *
 * `hoy` se puede fijar para que las pruebas no dependan del calendario.
 */
export function derivarAlertas(
  {
    vacunaciones = [],
    banos = [],
    servicios = [],
    diagnosticos = [],
    partos = [],
    potreros = [],
    guardadas = [],
  },
  hoy = new Date()
) {
  const referencia = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate())
  const yaResueltas = resueltas(guardadas)

  const todas = [
    ...porVacunaciones(vacunaciones, referencia),
    ...porBanos(banos, referencia),
    ...porPartos(servicios, diagnosticos, partos, referencia),
    ...porRotacion(potreros, referencia),
  ]
    .filter((alerta) => !yaResueltas.has(claveDe(alerta)))
    .filter((alerta) => alerta.dias <= HORIZONTE_DIAS)
    .sort((a, b) => a.dias - b.dias)

  return {
    vencidas: todas.filter((a) => a.urgencia === VENCIDA),
    estaSemana: todas.filter((a) => a.urgencia === ESTA_SEMANA),
    proximas: todas.filter((a) => a.urgencia === PROXIMA),
    total: todas.length,
  }
}

/** Cuantas hay sin atender. Es el numero que va en la barra de navegacion. */
export function contarPendientes(grupos) {
  return grupos.vencidas.length + grupos.estaSemana.length
}
