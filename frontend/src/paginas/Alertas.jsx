import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useDatosParaAlertas, useMarcarAlerta } from '../api/modulos'
import { usePotreros } from '../api/territorio'
import { derivarAlertas } from '../alertas/derivar'
import Boton from '../disenio/Boton'
import Caravana from '../disenio/Caravana'
import Fila from '../disenio/Fila'
import { fechaCorta } from './formato'

const MARCAS = { vencida: 'vencido', esta_semana: 'pronto', proxima: 'ok' }

const TIPO_ALERTA = {
  vacunacion: 'vacunacion',
  bano: 'bano',
  parto: 'parto',
  rotacion: 'rotacion',
}

function textoDePlazo(alerta) {
  if (alerta.dias < 0) {
    const dias = Math.abs(alerta.dias)
    return `Venció hace ${dias} ${dias === 1 ? 'día' : 'días'}`
  }
  if (alerta.dias === 0) return 'Vence hoy'
  if (alerta.dias === 1) return 'Mañana'
  return `En ${alerta.dias} días`
}

function Bloque({ titulo, alertas, alAtender, atendiendo }) {
  const navegar = useNavigate()
  if (!alertas.length) return null

  return (
    <>
      <h2 className="mb-2.5 mt-6 text-[15px] peso-medio">{titulo}</h2>
      <div className="divide-y divide-borde overflow-hidden rounded-caja border border-borde bg-superficie">
        {alertas.map((alerta) => (
          <Fila
            key={`${alerta.referencia_tabla}:${alerta.referencia_id}`}
            marca={MARCAS[alerta.urgencia]}
            izquierda={
              alerta.animal_id ? (
                <button
                  type="button"
                  onClick={() => navegar(`/animales/${alerta.animal_id}`)}
                  aria-label={`Abrir la ficha de ${alerta.arete}`}
                >
                  <Caravana arete={alerta.arete} tamano="chica" />
                </button>
              ) : (
                <Caravana arete={alerta.arete} tamano="chica" />
              )
            }
            titulo={alerta.titulo}
            meta={`${alerta.etiqueta} · ${textoDePlazo(alerta)}${
              alerta.fecha ? ` · ${fechaCorta(alerta.fecha)}` : ''
            }`}
            derecha={
              <Boton variante="suave" chico disabled={atendiendo} onClick={() => alAtender(alerta)}>
                Atender
              </Boton>
            }
          />
        ))}
      </div>
    </>
  )
}

/**
 * Alertas del hato.
 *
 * El calculo se hace aqui, en el dispositivo (decision 6): la pantalla junta
 * vacunas, baños, partos y potreros y deriva que esta vencido. Cuando la
 * Fase 2 lea esos datos de IndexedDB, esta pantalla no cambia.
 */
export default function Alertas() {
  const datos = useDatosParaAlertas()
  const potreros = usePotreros()
  const marcar = useMarcarAlerta()
  const [aviso, setAviso] = useState(null)

  const consultas = [
    datos.vacunaciones,
    datos.banos,
    datos.servicios,
    datos.diagnosticos,
    datos.partos,
    datos.guardadas,
    potreros,
  ]
  const cargando = consultas.some((c) => c.isPending)
  const fallo = consultas.find((c) => c.isError)

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

  const atender = async (alerta) => {
    await marcar.mutateAsync({
      tipo: TIPO_ALERTA[alerta.tipo] ?? 'otro',
      titulo: alerta.titulo,
      descripcion: alerta.detalle,
      estado: 'atendida',
      fecha_objetivo: alerta.fecha,
      animal_id: alerta.animal_id ?? undefined,
      referencia_tabla: alerta.referencia_tabla,
      referencia_id: alerta.referencia_id,
    })
    setAviso('Alerta marcada como atendida.')
    setTimeout(() => setAviso(null), 2600)
  }

  return (
    <div>
      <h1 className="text-[26px] peso-fuerte">Alertas</h1>
      <p className="mb-4 text-[13.5px] text-hierro">
        Se calculan en el teléfono con los datos que ya tienes.
      </p>

      {cargando && (
        <div className="rounded-caja border border-borde bg-superficie px-4 py-9 text-center text-[14px] text-hierro">
          Repasando el hato…
        </div>
      )}

      {fallo && (
        <div className="rounded-caja border border-borde bg-superficie px-4 py-9 text-center">
          <b className="mb-1 block text-[15.5px] peso-medio">No pudimos repasar el hato</b>
          <p className="mb-4 text-[13.5px] text-hierro">{fallo.error.message}</p>
          <Boton variante="suave" onClick={() => consultas.forEach((c) => c.refetch())}>
            Intentar otra vez
          </Boton>
        </div>
      )}

      {!cargando && !fallo && grupos.total === 0 && (
        <div className="rounded-caja border border-borde bg-superficie px-4 py-10 text-center">
          <b className="mb-1 block text-[15.5px] peso-medio">Todo al día</b>
          <p className="text-[13.5px] text-hierro">
            No hay vacunas, baños ni partos pendientes en los próximos tres meses.
          </p>
        </div>
      )}

      {!cargando && !fallo && (
        <>
          <Bloque
            titulo="Vencidas"
            alertas={grupos.vencidas}
            alAtender={atender}
            atendiendo={marcar.isPending}
          />
          <Bloque
            titulo="Esta semana"
            alertas={grupos.estaSemana}
            alAtender={atender}
            atendiendo={marcar.isPending}
          />
          <Bloque
            titulo="Próximas"
            alertas={grupos.proximas}
            alAtender={atender}
            atendiendo={marcar.isPending}
          />
        </>
      )}

      {aviso ? (
        <div className="fixed inset-x-3.5 bottom-[78px] z-[60] rounded-caja bg-tinta px-3.5 py-3 text-[14px] text-[#F2F5F0] rail:inset-x-auto rail:bottom-6 rail:right-6">
          {aviso}
        </div>
      ) : null}
    </div>
  )
}
