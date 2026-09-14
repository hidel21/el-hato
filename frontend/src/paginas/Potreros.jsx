import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { useLotes, usePotreros } from '../api/territorio'
import Boton from '../disenio/Boton'
import Etiqueta from '../disenio/Etiqueta'
import Fila from '../disenio/Fila'
import FormaLote from './FormaLote'
import FormaMovimiento from './FormaMovimiento'
import FormaPotrero from './FormaPotrero'
import { ETAPAS, numero } from './formato'

const NOMBRE_ETAPA = Object.fromEntries(ETAPAS)

/** Dias que lleva el ganado en el potrero. Se deriva en el cliente (decision 6). */
function diasOcupado(fechaIngreso) {
  if (!fechaIngreso) return null
  const dias = Math.floor((new Date() - new Date(`${fechaIngreso}T00:00:00`)) / 86400000)
  return dias >= 0 ? dias : null
}

function BarraCarga({ carga, capacidad }) {
  const actual = Number(carga ?? 0)
  const tope = Number(capacidad ?? 0)
  if (!tope) {
    return (
      <p className="mt-2.5 text-[12.5px] text-hierro">
        {numero(actual, 2)} UGM/ha · sin capacidad registrada
      </p>
    )
  }

  const porcentaje = Math.min(100, (actual / tope) * 100)
  const color = actual > tope ? 'bg-vencido' : porcentaje > 80 ? 'bg-pronto' : 'bg-pastoClaro'

  return (
    <>
      <div
        className="relative mb-1.5 mt-2.5 h-2.5 overflow-hidden rounded-full bg-[#EDF0E8]"
        role="img"
        aria-label={`Carga ${numero(actual, 2)} de ${numero(tope, 1)} unidades de ganado mayor por hectárea`}
      >
        <i className={`block h-full rounded-full ${color}`} style={{ width: `${porcentaje}%` }} />
      </div>
      <div className="flex justify-between text-[12.5px] text-hierro">
        <span>
          {numero(actual, 2)} de {numero(tope, 1)} UGM/ha
        </span>
        <span>{actual > tope ? 'Pasado de carga' : `${Math.round(porcentaje)}% de la carga`}</span>
      </div>
    </>
  )
}

function TarjetaPotrero({ potrero, alMover, alEditar }) {
  const dias = potrero.en_descanso ? null : diasOcupado(potrero.fecha_ultimo_ingreso)
  const rotar = dias !== null && dias > potrero.dias_descanso_recomendado

  return (
    <article className="p-3.5">
      <div className="flex items-baseline justify-between gap-2.5">
        <b className="text-[16px] peso-medio">{potrero.nombre}</b>
        <span className="text-[13px] text-hierro">{numero(potrero.hectareas, 0)} ha</span>
      </div>

      <p className="mt-px text-[13px] text-hierro">
        {potrero.en_descanso
          ? 'En descanso'
          : `${potrero.cantidad_animales} ${potrero.cantidad_animales === 1 ? 'animal' : 'animales'}`}
        {potrero.lotes.length ? ` · ${potrero.lotes.join(', ')}` : ''}
        {dias !== null ? ` · ${dias} ${dias === 1 ? 'día' : 'días'} ocupado` : ''}
      </p>

      <BarraCarga carga={potrero.carga_ugm_ha} capacidad={potrero.capacidad_ugm_ha} />

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {rotar && (
          <Etiqueta tono="pronto">
            Pasó los {potrero.dias_descanso_recomendado} días recomendados
          </Etiqueta>
        )}
        <Boton variante="suave" chico onClick={alMover}>
          Mover ganado
        </Boton>
        <Boton variante="suave" chico onClick={alEditar}>
          Editar
        </Boton>
      </div>
    </article>
  )
}

function Estado({ consulta, vacio, children }) {
  if (consulta.isPending) {
    return <p className="px-4 py-9 text-center text-[14px] text-hierro">Trayendo el campo…</p>
  }
  if (consulta.isError) {
    return (
      <div className="px-4 py-9 text-center">
        <b className="mb-1 block text-[15.5px] peso-medio">No pudimos traer esto</b>
        <p className="mb-4 text-[13.5px] text-hierro">{consulta.error.message}</p>
        <Boton variante="suave" onClick={() => consulta.refetch()}>
          Intentar otra vez
        </Boton>
      </div>
    )
  }
  if (!consulta.data?.length) return vacio
  return children
}

export default function Potreros() {
  const navegar = useNavigate()
  const [parametros, setParametros] = useSearchParams()
  const [pestana, setPestana] = useState('potreros')
  const [formaPotrero, setFormaPotrero] = useState(null) // null | {} | potrero
  const [formaLote, setFormaLote] = useState(false)
  const [loteAMover, setLoteAMover] = useState(null)

  const potreros = usePotreros()
  const lotes = useLotes()

  // La hoja de registro rapido abre el movimiento con ?mover=1
  const moverAbierto = loteAMover !== null || parametros.get('mover') === '1'
  const cerrarMover = () => {
    setLoteAMover(null)
    if (parametros.get('mover')) {
      parametros.delete('mover')
      setParametros(parametros, { replace: true })
    }
  }

  const hectareas = (potreros.data ?? []).reduce((suma, p) => suma + Number(p.hectareas), 0)
  const animales = (potreros.data ?? []).reduce((suma, p) => suma + p.cantidad_animales, 0)

  return (
    <div>
      <h1 className="text-[26px] peso-fuerte">Potreros</h1>
      <p className="mb-4 text-[13.5px] text-hierro">
        {potreros.isSuccess
          ? `${potreros.data.length} potreros · ${numero(hectareas, 0)} hectáreas · ${animales} animales en campo`
          : 'Trayendo el campo'}
      </p>

      <div className="mb-4 flex gap-0.5 border-b border-borde" role="tablist">
        {[
          ['potreros', 'Potreros'],
          ['lotes', 'Lotes'],
        ].map(([clave, texto]) => (
          <button
            key={clave}
            type="button"
            role="tab"
            aria-selected={pestana === clave}
            onClick={() => setPestana(clave)}
            className={`-mb-px flex-none px-3 py-3 text-[14px] ${
              pestana === clave
                ? 'border-b-2 border-caravana text-tinta peso-medio'
                : 'border-b-2 border-transparent text-hierro'
            }`}
          >
            {texto}
          </button>
        ))}
      </div>

      {pestana === 'potreros' ? (
        <>
          <div className="divide-y divide-borde overflow-hidden rounded-caja border border-borde bg-superficie">
            <Estado
              consulta={potreros}
              vacio={
                <div className="px-4 py-9 text-center">
                  <b className="mb-1 block text-[15.5px] peso-medio">Todavía no hay potreros</b>
                  <p className="mb-4 text-[13.5px] text-hierro">
                    Registra el primero y empieza a llevar la rotación del pasto.
                  </p>
                  <Boton variante="amarillo" onClick={() => setFormaPotrero({})}>
                    Crear un potrero
                  </Boton>
                </div>
              }
            >
              {(potreros.data ?? []).map((potrero) => (
                <TarjetaPotrero
                  key={potrero.id}
                  potrero={potrero}
                  alMover={() => setLoteAMover('')}
                  alEditar={() => setFormaPotrero(potrero)}
                />
              ))}
            </Estado>
          </div>

          {potreros.data?.length ? (
            <Boton variante="suave" bloque className="mt-3" onClick={() => setFormaPotrero({})}>
              Crear un potrero
            </Boton>
          ) : null}
        </>
      ) : (
        <>
          <div className="divide-y divide-borde overflow-hidden rounded-caja border border-borde bg-superficie">
            <Estado
              consulta={lotes}
              vacio={
                <div className="px-4 py-9 text-center">
                  <b className="mb-1 block text-[15.5px] peso-medio">Todavía no hay lotes</b>
                  <p className="mb-4 text-[13.5px] text-hierro">
                    Un lote junta a los animales que se manejan igual: los vientres, el levante, las
                    terneras del año.
                  </p>
                  <Boton variante="amarillo" onClick={() => setFormaLote(true)}>
                    Crear un lote
                  </Boton>
                </div>
              }
            >
              {(lotes.data ?? []).map((lote) => (
                <Fila
                  key={lote.id}
                  onClick={() => navegar(`/animales?lote=${lote.id}`)}
                  titulo={
                    <>
                      {lote.nombre}
                      <Etiqueta>{NOMBRE_ETAPA[lote.etapa] ?? lote.etapa}</Etiqueta>
                    </>
                  }
                  meta={lote.potrero_nombre ?? 'Sin potrero asignado'}
                  derecha={
                    <>
                      <b className="block text-[15px] peso-medio">{lote.cantidad_animales}</b>
                      <span className="block text-[12.5px] text-hierro">
                        {lote.cantidad_animales === 1 ? 'animal' : 'animales'}
                      </span>
                    </>
                  }
                />
              ))}
            </Estado>
          </div>

          {lotes.data?.length ? (
            <div className="mt-3 flex flex-col gap-2 rail:flex-row">
              <Boton variante="suave" bloque onClick={() => setFormaLote(true)}>
                Crear un lote
              </Boton>
              <Boton variante="suave" bloque onClick={() => setLoteAMover('')}>
                Mover ganado
              </Boton>
            </div>
          ) : null}
        </>
      )}

      <FormaPotrero
        abierta={formaPotrero !== null}
        potrero={formaPotrero?.id ? formaPotrero : null}
        alCerrar={() => setFormaPotrero(null)}
      />
      <FormaLote abierta={formaLote} alCerrar={() => setFormaLote(false)} />
      <FormaMovimiento
        abierta={moverAbierto}
        loteInicial={loteAMover || ''}
        alCerrar={cerrarMover}
      />
    </div>
  )
}
