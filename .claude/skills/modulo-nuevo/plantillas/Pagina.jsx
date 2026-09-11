import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useRegistros } from '../api/modulo'
import Boton from '../disenio/Boton'
import Buscador from '../disenio/Buscador'
import Caravana from '../disenio/Caravana'
import Fila from '../disenio/Fila'

/**
 * Plantilla de pantalla de listado. Los tres estados son obligatorios:
 * cargando, error con reintento y lista vacia que invita a actuar.
 */
export default function Pagina() {
  const navegar = useNavigate()
  const [texto, setTexto] = useState('')
  const listado = useRegistros({ buscar: texto })
  const registros = listado.data?.pages.flatMap((pagina) => pagina.datos) ?? []

  return (
    <div>
      <h1 className="text-[26px] peso-fuerte">Titulo</h1>
      <p className="mb-4 text-[13.5px] text-hierro">Una linea que diga que hay aqui.</p>

      <Buscador valor={texto} alCambiar={setTexto} marcador="Buscar" />

      <div className="mt-3 overflow-hidden rounded-caja border border-borde bg-superficie">
        {listado.isPending && (
          <p className="px-4 py-9 text-center text-[14px] text-hierro">Trayendo los registros…</p>
        )}

        {listado.isError && (
          <div className="px-4 py-9 text-center">
            <b className="mb-1 block text-[15.5px] peso-medio">No pudimos traer los registros</b>
            <p className="mb-4 text-[13.5px] text-hierro">{listado.error.message}</p>
            <Boton variante="suave" onClick={() => listado.refetch()}>
              Intentar otra vez
            </Boton>
          </div>
        )}

        {listado.isSuccess && registros.length === 0 && (
          <div className="px-4 py-9 text-center">
            <b className="mb-1 block text-[15.5px] peso-medio">Todavia no hay nada aqui</b>
            <p className="mb-4 text-[13.5px] text-hierro">
              Registra el primero y empieza a llevar la cuenta.
            </p>
            <Boton variante="amarillo" onClick={() => navegar('/ruta/nuevo')}>
              Registrar
            </Boton>
          </div>
        )}

        {registros.map((registro, indice) => (
          <div key={registro.id} className={indice ? 'border-t border-borde' : ''}>
            <Fila
              onClick={() => navegar(`/ruta/${registro.id}`)}
              izquierda={<Caravana arete={registro.animal_arete} />}
              titulo={registro.titulo}
              meta={registro.meta}
              derecha={<b className="block text-[15px] peso-medio">{registro.cifra}</b>}
            />
          </div>
        ))}
      </div>

      {listado.hasNextPage && (
        <Boton
          variante="suave"
          bloque
          className="mt-3"
          disabled={listado.isFetchingNextPage}
          onClick={() => listado.fetchNextPage()}
        >
          {listado.isFetchingNextPage ? 'Cargando…' : 'Ver más'}
        </Boton>
      )}
    </div>
  )
}
