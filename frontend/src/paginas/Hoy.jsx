import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useDatosParaAlertas, useInventario, usePesajesRecientes } from '../api/modulos'
import { usePotreros } from '../api/territorio'
import { derivarAlertas } from '../alertas/derivar'
import Caravana from '../disenio/Caravana'
import Etiqueta from '../disenio/Etiqueta'
import Fila from '../disenio/Fila'
import { IconoBano, IconoCelo, IconoPesaje, IconoVacuna } from '../disenio/iconos'
import FormaRegistro from '../registro/FormaRegistro'
import { numero } from './formato'

const ATAJOS = [
  ['pesaje', 'Pesaje', IconoPesaje],
  ['vacuna', 'Vacuna', IconoVacuna],
  ['celo', 'Celo', IconoCelo],
  ['bano', 'Baño', IconoBano],
]

const MARCAS = { vencida: 'vencido', esta_semana: 'pronto', proxima: 'ok' }

function fechaLarga(hoy = new Date()) {
  const texto = hoy.toLocaleDateString('es-CO', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

function esDeHoy(marca) {
  if (!marca) return false
  return new Date(marca).toDateString() === new Date().toDateString()
}

function Cifra({ valor, rotulo }) {
  return (
    <div className="bg-superficie px-3.5 py-3">
      <b className="block text-[24px] leading-tight peso-fuerte">{valor}</b>
      <span className="mt-0.5 block text-[12.5px] text-hierro">{rotulo}</span>
    </div>
  )
}

/**
 * La pantalla del dia.
 *
 * Es lo primero que ve el capataz cuando abre la aplicacion en el potrero:
 * que hay que hacer hoy, un atajo para registrarlo, y que ya quedo hecho.
 */
export default function Hoy() {
  const navegar = useNavigate()
  const [accion, setAccion] = useState(null)

  const inventario = useInventario()
  const potreros = usePotreros()
  const pesajes = usePesajesRecientes(10)
  const datos = useDatosParaAlertas()

  const grupos = useMemo(
    () =>
      derivarAlertas({
        vacunaciones: datos.vacunaciones.data ?? [],
        banos: datos.banos.data ?? [],
        servicios: datos.servicios.data ?? [],
        diagnosticos: datos.diagnosticos.data ?? [],
        partos: datos.partos.data ?? [],
        potreros: potreros.data ?? [],
        guardadas: datos.guardadas.data ?? [],
      }),
    [
      datos.vacunaciones.data,
      datos.banos.data,
      datos.servicios.data,
      datos.diagnosticos.data,
      datos.partos.data,
      datos.guardadas.data,
      potreros.data,
    ]
  )

  const urgentes = [...grupos.vencidas, ...grupos.estaSemana].slice(0, 4)

  // Lo registrado hoy, junto de todos los modulos.
  const bitacora = useMemo(() => {
    const filas = [
      ...(pesajes.data ?? [])
        .filter((p) => esDeHoy(p.created_at))
        .map((p) => ({
          id: `pesaje-${p.id}`,
          arete: p.animal_arete ?? '—',
          titulo: `Pesaje ${numero(p.peso_kg)} kg`,
          meta: p.ganancia_diaria_kg
            ? `${numero(p.ganancia_diaria_kg, 2)} kg/día`
            : 'Primer pesaje',
          cuando: p.created_at,
        })),
      ...(datos.vacunaciones.data ?? [])
        .filter((v) => esDeHoy(v.created_at))
        .map((v) => ({
          id: `vacuna-${v.id}`,
          arete: v.animal_arete ?? 'Lote',
          titulo: `${v.vacuna_nombre} a ${v.cantidad_animales} ${
            v.cantidad_animales === 1 ? 'animal' : 'animales'
          }`,
          meta: v.grupo_nombre ?? 'Aplicación individual',
          cuando: v.created_at,
        })),
      ...(datos.banos.data ?? [])
        .filter((b) => esDeHoy(b.created_at))
        .map((b) => ({
          id: `bano-${b.id}`,
          arete: 'Lote',
          titulo: `${b.producto_nombre} a ${b.cantidad_animales} animales`,
          meta: b.grupo_nombre ?? b.potrero_nombre ?? '',
          cuando: b.created_at,
        })),
    ]
    return filas.sort((a, b) => (a.cuando < b.cuando ? 1 : -1)).slice(0, 6)
  }, [pesajes.data, datos.vacunaciones.data, datos.banos.data])

  const totales = inventario.data
  const porEtapa = Object.fromEntries(
    (totales?.por_etapa ?? []).map((corte) => [corte.clave, corte.cantidad])
  )

  return (
    <div>
      <h1 className="text-[26px] peso-fuerte">{fechaLarga()}</h1>
      <p className="mb-4 text-[13.5px] text-hierro">
        {grupos.vencidas.length + grupos.estaSemana.length > 0
          ? `Tienes ${grupos.vencidas.length + grupos.estaSemana.length} pendientes de campo.`
          : 'No tienes pendientes de campo.'}
      </p>

      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-caja border border-borde bg-borde doble:grid-cols-4">
        <Cifra valor={totales?.total_animales ?? '—'} rotulo="Animales" />
        <Cifra valor={porEtapa.vientre ?? 0} rotulo="Vientres" />
        <Cifra valor={(porEtapa.engorde ?? 0) + (porEtapa.levante ?? 0)} rotulo="En engorde" />
        <Cifra
          valor={totales?.gdp_promedio_kg ? numero(totales.gdp_promedio_kg, 2) : '—'}
          rotulo="Ganancia kg/día"
        />
      </div>

      <h2 className="mb-2.5 mt-6 text-[15px] peso-medio">Registrar en el potrero</h2>
      <div className="grid grid-cols-4 gap-2">
        {ATAJOS.map(([clave, texto, Icono]) => (
          <button
            key={clave}
            type="button"
            onClick={() => setAccion(clave)}
            className="flex min-h-[74px] flex-col items-center justify-center gap-1.5 rounded-caja border border-borde bg-superficie px-1.5 py-3 text-[12.5px] peso-medio hover:border-pastoClaro"
          >
            <Icono className="h-[22px] w-[22px] stroke-pasto" />
            {texto}
          </button>
        ))}
      </div>

      <h2 className="mb-2.5 mt-6 text-[15px] peso-medio">Lo que urge</h2>
      {urgentes.length ? (
        <div className="divide-y divide-borde overflow-hidden rounded-caja border border-borde bg-superficie">
          {urgentes.map((alerta) => (
            <Fila
              key={`${alerta.referencia_tabla}:${alerta.referencia_id}`}
              marca={MARCAS[alerta.urgencia]}
              onClick={() => navegar('/alertas')}
              titulo={alerta.titulo}
              meta={`${alerta.etiqueta} · ${alerta.detalle}`}
              derecha={
                <Etiqueta tono={alerta.urgencia === 'vencida' ? 'vencido' : 'pronto'}>
                  {alerta.dias < 0 ? 'Vencido' : alerta.dias === 0 ? 'Hoy' : `${alerta.dias} días`}
                </Etiqueta>
              }
            />
          ))}
        </div>
      ) : (
        <div className="rounded-caja border border-borde bg-superficie px-4 py-8 text-center">
          <b className="mb-1 block text-[15.5px] peso-medio">Nada pendiente</b>
          <p className="text-[13.5px] text-hierro">
            Ni vacunas ni baños ni partos para esta semana.
          </p>
        </div>
      )}

      <h2 className="mb-2.5 mt-6 text-[15px] peso-medio">Lo que registraste hoy</h2>
      {bitacora.length ? (
        <div className="divide-y divide-borde overflow-hidden rounded-caja border border-borde bg-superficie">
          {bitacora.map((fila) => (
            <Fila
              key={fila.id}
              izquierda={<Caravana arete={fila.arete} tamano="chica" />}
              titulo={fila.titulo}
              meta={fila.meta}
            />
          ))}
        </div>
      ) : (
        <div className="rounded-caja border border-borde bg-superficie px-4 py-8 text-center">
          <b className="mb-1 block text-[15.5px] peso-medio">Todavía nada</b>
          <p className="text-[13.5px] text-hierro">
            Lo que registres hoy en el potrero aparece aquí.
          </p>
        </div>
      )}

      <FormaRegistro accion={accion} abierta={accion !== null} alCerrar={() => setAccion(null)} />
    </div>
  )
}
