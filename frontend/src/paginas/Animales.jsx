import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { useAnimales } from '../api/animales'
import { useLotes } from '../api/territorio'
import { useMedia } from '../armazon/useMedia'
import Boton from '../disenio/Boton'
import Buscador from '../disenio/Buscador'
import Caravana from '../disenio/Caravana'
import Etiqueta from '../disenio/Etiqueta'
import Fila from '../disenio/Fila'
import AnimalFicha from './AnimalFicha'
import { ESTADOS, edad, kilos } from './formato'

const FILTROS = [
  { clave: 'todos', texto: 'Todos', estado: undefined },
  { clave: 'activo', texto: 'Activos', estado: 'activo' },
  { clave: 'en_engorde', texto: 'En engorde', estado: 'en_engorde' },
  { clave: 'vendido', texto: 'Vendidos', estado: 'vendido' },
]

/** Espera a que el capataz deje de teclear antes de pedir a la API. */
function useRetraso(valor, milisegundos = 300) {
  const [retrasado, setRetrasado] = useState(valor)
  useEffect(() => {
    const reloj = setTimeout(() => setRetrasado(valor), milisegundos)
    return () => clearTimeout(reloj)
  }, [valor, milisegundos])
  return retrasado
}

export default function Animales() {
  const { id } = useParams()
  const navegar = useNavigate()
  const dosPaneles = useMedia('(min-width: 1100px)')

  const [parametros, setParametros] = useSearchParams()
  const [texto, setTexto] = useState('')
  const [filtro, setFiltro] = useState('todos')
  const buscar = useRetraso(texto)

  // El lote llega por la URL: desde la pantalla de potreros se entra ya filtrado.
  const loteId = parametros.get('lote')
  const lotes = useLotes()
  const lote = (lotes.data ?? []).find((l) => l.id === loteId)

  const quitarLote = () => {
    parametros.delete('lote')
    setParametros(parametros, { replace: true })
  }

  const estado = FILTROS.find((f) => f.clave === filtro)?.estado
  const listado = useAnimales({ buscar, estado, grupo_id: loteId ?? undefined })

  const animales = listado.data?.pages.flatMap((pagina) => pagina.datos) ?? []

  // En pantalla chica la ficha ocupa toda la vista.
  if (id && !dosPaneles) return <AnimalFicha id={id} conVolver />

  const lista = (
    <div>
      <h1 className="text-[26px] peso-fuerte">Animales</h1>
      <p className="mb-4 text-[13.5px] text-hierro">
        {listado.isSuccess
          ? `${animales.length} ${animales.length === 1 ? 'ficha' : 'fichas'}${
              listado.hasNextPage ? ' cargadas' : ''
            }`
          : 'Trayendo el hato'}
      </p>

      <Buscador valor={texto} alCambiar={setTexto} marcador="Buscar por arete o nombre" />

      {loteId && (
        <button
          type="button"
          onClick={quitarLote}
          className="mt-3 flex min-h-[40px] w-full items-center justify-between gap-2 rounded-caja border border-pasto bg-[#F2F6F0] px-3.5 text-left text-[13.5px] peso-medio"
        >
          <span>Solo el lote {lote?.nombre ?? 'elegido'}</span>
          <span className="text-hierro">Ver todos ✕</span>
        </button>
      )}

      <div className="-mx-3.5 flex gap-[7px] overflow-x-auto px-3.5 py-3 [scrollbar-width:none] rail:mx-0 rail:px-0">
        {FILTROS.map((opcion) => (
          <button
            key={opcion.clave}
            type="button"
            aria-pressed={filtro === opcion.clave}
            onClick={() => setFiltro(opcion.clave)}
            className={`flex-none whitespace-nowrap rounded-full border px-3.5 py-[7px] text-[13.5px] peso-medio ${
              filtro === opcion.clave
                ? 'border-pasto bg-pasto text-white'
                : 'border-borde bg-superficie text-tinta'
            }`}
          >
            {opcion.texto}
          </button>
        ))}
      </div>

      <div className="overflow-hidden rounded-caja border border-borde bg-superficie">
        {listado.isPending && (
          <p className="px-4 py-9 text-center text-[14px] text-hierro">Trayendo los animales…</p>
        )}

        {listado.isError && (
          <div className="px-4 py-9 text-center">
            <b className="mb-1 block text-[15.5px] peso-medio">No pudimos traer el hato</b>
            <p className="mb-4 text-[13.5px] text-hierro">{listado.error.message}</p>
            <Boton variante="suave" onClick={() => listado.refetch()}>
              Intentar otra vez
            </Boton>
          </div>
        )}

        {listado.isSuccess && animales.length === 0 && (
          <div className="px-4 py-9 text-center">
            <b className="mb-1 block text-[15.5px] peso-medio">
              {buscar || loteId ? 'Ningún animal coincide' : 'Todavía no hay animales'}
            </b>
            <p className="mb-4 text-[13.5px] text-hierro">
              {buscar || loteId
                ? 'Revisa el arete o quita los filtros.'
                : 'Da de alta la primera ficha y empieza a llevar el hato.'}
            </p>
            <Boton variante="amarillo" onClick={() => navegar('/animales/nuevo')}>
              Dar de alta un animal
            </Boton>
          </div>
        )}

        {animales.map((animal, indice) => {
          const marcaEstado = ESTADOS[animal.estado] ?? { texto: animal.estado, tono: 'neutro' }
          return (
            <div key={animal.id} className={indice ? 'border-t border-borde' : ''}>
              <Fila
                activa={dosPaneles && animal.id === id}
                onClick={() => navegar(`/animales/${animal.id}`)}
                izquierda={<Caravana arete={animal.arete} />}
                titulo={
                  <>
                    {animal.nombre ?? 'Sin nombre'}
                    {animal.arete_duplicado && <Etiqueta tono="pronto">Arete repetido</Etiqueta>}
                  </>
                }
                meta={[animal.raza, edad(animal.fecha_nacimiento), animal.potrero_nombre]
                  .filter(Boolean)
                  .join(' · ')}
                derecha={
                  <>
                    <b className="block text-[15px] peso-medio">
                      {kilos(animal.peso_actual_kg) ?? '—'}
                    </b>
                    <span className="block text-[12.5px] text-hierro">{marcaEstado.texto}</span>
                  </>
                }
              />
            </div>
          )
        })}
      </div>

      {listado.hasNextPage && (
        <Boton
          variante="suave"
          bloque
          className="mt-3"
          disabled={listado.isFetchingNextPage}
          onClick={() => listado.fetchNextPage()}
        >
          {listado.isFetchingNextPage ? 'Cargando…' : 'Ver más animales'}
        </Boton>
      )}
    </div>
  )

  if (!dosPaneles) return lista

  return (
    <div className="grid grid-cols-[minmax(320px,380px)_1fr] items-start gap-6">
      {lista}
      <div className="sticky top-[22px]">
        {id ? (
          <AnimalFicha id={id} />
        ) : (
          <div className="rounded-caja border border-borde bg-superficie px-4 py-12 text-center">
            <b className="mb-1 block text-[15.5px] peso-medio">Elige un animal</b>
            <p className="text-[13.5px] text-hierro">
              Toca una ficha de la lista para ver su historia.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
