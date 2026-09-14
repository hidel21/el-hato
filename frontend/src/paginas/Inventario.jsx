import { useInventario } from '../api/modulos'
import Boton from '../disenio/Boton'
import Fila from '../disenio/Fila'
import { numero } from './formato'

function Cifra({ valor, rotulo }) {
  return (
    <div className="bg-superficie px-3.5 py-3">
      <b className="block text-[24px] leading-tight peso-fuerte">{valor}</b>
      <span className="mt-0.5 block text-[12.5px] text-hierro">{rotulo}</span>
    </div>
  )
}

function Corte({ titulo, cortes }) {
  if (!cortes.length) return null
  return (
    <>
      <h2 className="mb-2.5 mt-6 text-[15px] peso-medio">{titulo}</h2>
      <div className="divide-y divide-borde overflow-hidden rounded-caja border border-borde bg-superficie">
        {cortes.map((corte) => (
          <Fila
            key={corte.clave}
            titulo={corte.etiqueta}
            meta={`${corte.porcentaje}% del hato`}
            derecha={<b className="block text-[15px] peso-medio">{corte.cantidad}</b>}
          />
        ))}
      </div>
    </>
  )
}

/**
 * Inventario del hato.
 *
 * Sale de la vista materializada, que se refresca aparte con debounce de 30
 * segundos (decision 7). Por eso la pantalla dice de cuando son los numeros:
 * mentir sobre eso es peor que llegar tarde.
 */
export default function Inventario() {
  const inventario = useInventario()

  if (inventario.isPending) {
    return <p className="px-1 py-9 text-center text-[14px] text-hierro">Contando el hato…</p>
  }

  if (inventario.isError) {
    return (
      <div className="rounded-caja border border-borde bg-superficie px-4 py-9 text-center">
        <b className="mb-1 block text-[15.5px] peso-medio">No pudimos contar el hato</b>
        <p className="mb-4 text-[13.5px] text-hierro">{inventario.error.message}</p>
        <Boton variante="suave" onClick={() => inventario.refetch()}>
          Intentar otra vez
        </Boton>
      </div>
    )
  }

  const datos = inventario.data
  const actualizado = datos.actualizado_en
    ? new Date(datos.actualizado_en).toLocaleString('es-CO', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      })
    : null

  if (!datos.total_animales) {
    return (
      <div>
        <h1 className="text-[26px] peso-fuerte">Inventario del hato</h1>
        <div className="mt-4 rounded-caja border border-borde bg-superficie px-4 py-10 text-center">
          <b className="mb-1 block text-[15.5px] peso-medio">Todavía no hay animales</b>
          <p className="text-[13.5px] text-hierro">
            Cuando des de alta las primeras fichas, aquí aparece el conteo.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-[26px] peso-fuerte">Inventario del hato</h1>
      <p className="mb-4 text-[13.5px] text-hierro">
        {actualizado ? `Contado el ${actualizado}` : 'Calculado desde las fichas'}
      </p>

      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-caja border border-borde bg-borde doble:grid-cols-4">
        <Cifra valor={datos.total_animales} rotulo="Animales" />
        <Cifra valor={datos.hembras} rotulo="Hembras" />
        <Cifra valor={datos.machos} rotulo="Machos" />
        <Cifra
          valor={datos.gdp_promedio_kg ? numero(datos.gdp_promedio_kg, 2) : '—'}
          rotulo="Ganancia diaria kg"
        />
      </div>

      <div className="mt-3 grid grid-cols-2 gap-px overflow-hidden rounded-caja border border-borde bg-borde">
        <Cifra valor={`${numero(datos.peso_total_kg, 0)} kg`} rotulo="Peso total del hato" />
        <Cifra
          valor={datos.peso_promedio_kg ? `${numero(datos.peso_promedio_kg, 0)} kg` : '—'}
          rotulo="Peso promedio"
        />
      </div>

      <Corte titulo="Por etapa" cortes={datos.por_etapa} />
      <Corte titulo="Por potrero" cortes={datos.por_potrero} />
      <Corte titulo="Por estado" cortes={datos.por_estado} />
    </div>
  )
}
