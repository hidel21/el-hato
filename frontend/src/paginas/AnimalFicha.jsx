import { useNavigate } from 'react-router-dom'

import { useAnimal, useGenealogia } from '../api/animales'
import Boton from '../disenio/Boton'
import Caravana from '../disenio/Caravana'
import Etiqueta from '../disenio/Etiqueta'
import { IconoVolver } from '../disenio/iconos'
import { ESTADOS, SEXOS, edad, fechaCorta, kilos } from './formato'

function Dato({ rotulo, children }) {
  return (
    <div className="bg-superficie px-3.5 py-2.5">
      <span className="block text-xs text-hierro">{rotulo}</span>
      <b className="mt-px block text-[15px] peso-medio">{children ?? '—'}</b>
    </div>
  )
}

function Pariente({ rotulo, nodo }) {
  return (
    <div className="rounded-caja border border-borde bg-superficie px-3.5 py-3">
      <span className="mb-1.5 block text-xs text-hierro">{rotulo}</span>
      {nodo ? (
        <div className="flex flex-wrap items-center gap-2">
          <Caravana arete={nodo.arete} tamano="chica" />
          <b className="text-[15px] peso-medio">{nodo.nombre ?? 'Sin nombre'}</b>
        </div>
      ) : (
        <span className="text-[14px] text-hierro">Sin registrar</span>
      )}
    </div>
  )
}

export default function AnimalFicha({ id, conVolver = false }) {
  const navegar = useNavigate()
  const ficha = useAnimal(id)
  const arbol = useGenealogia(id)

  if (ficha.isPending) {
    return <p className="px-1 py-8 text-center text-[14px] text-hierro">Abriendo la ficha…</p>
  }

  if (ficha.isError) {
    return (
      <div className="rounded-caja border border-borde bg-superficie px-4 py-8 text-center">
        <b className="mb-1 block text-[15.5px] peso-medio">No pudimos abrir la ficha</b>
        <p className="mb-4 text-[13.5px] text-hierro">{ficha.error.message}</p>
        <Boton variante="suave" onClick={() => ficha.refetch()}>
          Intentar otra vez
        </Boton>
      </div>
    )
  }

  const animal = ficha.data
  const estado = ESTADOS[animal.estado] ?? { texto: animal.estado, tono: 'neutro' }
  const raiz = arbol.data?.animal

  return (
    <article>
      {conVolver && (
        <button
          type="button"
          onClick={() => navegar('/animales')}
          className="mb-1 flex items-center gap-1.5 py-2 text-[14px] text-hierro peso-medio"
        >
          <IconoVolver className="h-4 w-4 stroke-current" />
          Animales
        </button>
      )}

      <div className="mb-1 flex flex-wrap items-start gap-3">
        <Caravana arete={animal.arete} tamano="grande" />
        <div className="min-w-[140px] flex-1">
          <h1 className="text-[23px] peso-fuerte">{animal.nombre ?? 'Sin nombre'}</h1>
          <p className="text-[13.5px] text-hierro">
            {[animal.raza, SEXOS[animal.sexo], edad(animal.fecha_nacimiento)]
              .filter(Boolean)
              .join(' · ')}
          </p>
        </div>
        <Etiqueta tono={estado.tono}>{estado.texto}</Etiqueta>
      </div>

      {animal.arete_duplicado && (
        <p className="mt-3 rounded-caja border border-[#EEDCBC] bg-[#FEF8EC] px-3.5 py-2.5 text-[13.5px] text-pronto">
          Este arete está repetido en la finca. Hay una alerta abierta para resolverlo.
        </p>
      )}

      <div className="mt-3.5 grid grid-cols-2 gap-px overflow-hidden rounded-caja border border-borde bg-borde doble:grid-cols-4">
        <Dato rotulo="Último peso">{kilos(animal.peso_actual_kg)}</Dato>
        <Dato rotulo="Nacimiento">{fechaCorta(animal.fecha_nacimiento)}</Dato>
        <Dato rotulo="Grupo">{animal.grupo_nombre}</Dato>
        <Dato rotulo="Potrero">{animal.potrero_nombre}</Dato>
      </div>

      <h2 className="mb-2.5 mt-6 text-[15px] peso-medio">Genealogía</h2>
      {arbol.isPending ? (
        <p className="text-[13.5px] text-hierro">Buscando padres y abuelos…</p>
      ) : arbol.isError ? (
        <p className="text-[13.5px] text-hierro">No pudimos traer la genealogía.</p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-2.5">
            <Pariente rotulo="Madre" nodo={raiz?.madre} />
            <Pariente rotulo="Padre" nodo={raiz?.padre} />
          </div>
          {(raiz?.madre?.madre || raiz?.madre?.padre || raiz?.padre?.madre) && (
            <>
              <h3 className="mb-2.5 mt-3.5 text-[13px] text-hierro">Abuelos</h3>
              <div className="grid grid-cols-2 gap-2.5">
                <Pariente rotulo="Madre de la madre" nodo={raiz?.madre?.madre} />
                <Pariente rotulo="Padre de la madre" nodo={raiz?.madre?.padre} />
              </div>
            </>
          )}
        </>
      )}

      {animal.observaciones && (
        <>
          <h2 className="mb-2.5 mt-6 text-[15px] peso-medio">Notas</h2>
          <p className="rounded-caja border border-borde bg-superficie px-3.5 py-3 text-[14px]">
            {animal.observaciones}
          </p>
        </>
      )}
    </article>
  )
}
