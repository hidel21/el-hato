import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAnimal, useGenealogia } from '../api/animales'
import {
  useGastosDeAnimal,
  useHistorialPeso,
  useHojaReproductiva,
  useSanidadDeAnimal,
} from '../api/modulos'
import Boton from '../disenio/Boton'
import Caravana from '../disenio/Caravana'
import Etiqueta from '../disenio/Etiqueta'
import Fila from '../disenio/Fila'
import { IconoVolver } from '../disenio/iconos'
import FormaRegistro from '../registro/FormaRegistro'
import { ESTADOS, SEXOS, edad, fechaCorta, kilos, numero } from './formato'
import GraficaPeso from './GraficaPeso'

const PESTANAS = [
  ['resumen', 'Resumen'],
  ['peso', 'Peso'],
  ['sanidad', 'Sanidad'],
  ['repro', 'Reproducción'],
  ['gastos', 'Gastos'],
]

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

function Vacio({ children }) {
  return (
    <div className="rounded-caja border border-borde bg-superficie px-4 py-8 text-center text-[13.5px] text-hierro">
      {children}
    </div>
  )
}

function Lista({ children }) {
  return (
    <div className="divide-y divide-borde overflow-hidden rounded-caja border border-borde bg-superficie">
      {children}
    </div>
  )
}

function PanelPeso({ animalId }) {
  const historial = useHistorialPeso(animalId)
  if (historial.isPending) return <p className="text-[13.5px] text-hierro">Trayendo los pesos…</p>
  if (historial.isError) return <Vacio>No pudimos traer los pesajes.</Vacio>

  const pesajes = historial.data
  if (!pesajes.length) {
    return <Vacio>Todavía no lo han pesado. Regístrale un pesaje y aparece la evolución.</Vacio>
  }

  return (
    <>
      <GraficaPeso pesajes={pesajes} />
      <div className="mt-3">
        <Lista>
          {[...pesajes].reverse().map((pesaje) => (
            <Fila
              key={pesaje.id}
              titulo={`${numero(pesaje.peso_kg)} kg`}
              meta={`${fechaCorta(pesaje.fecha_pesaje)}${pesaje.metodo ? ` · ${pesaje.metodo}` : ''}`}
              derecha={
                pesaje.diferencia_kg !== null && pesaje.diferencia_kg !== undefined ? (
                  <>
                    <b
                      className={`block text-[15px] peso-medio ${
                        Number(pesaje.diferencia_kg) >= 0 ? 'text-ok' : 'text-vencido'
                      }`}
                    >
                      {Number(pesaje.diferencia_kg) >= 0 ? '+' : ''}
                      {numero(pesaje.diferencia_kg)} kg
                    </b>
                    <span className="block text-[12.5px] text-hierro">
                      {pesaje.ganancia_diaria_kg
                        ? `${numero(pesaje.ganancia_diaria_kg, 2)} kg/día`
                        : `${pesaje.dias_desde_anterior} días`}
                    </span>
                  </>
                ) : (
                  <span className="text-[12.5px] text-hierro">primer pesaje</span>
                )
              }
            />
          ))}
        </Lista>
      </div>
    </>
  )
}

function PanelSanidad({ animalId }) {
  const { vacunas, banos } = useSanidadDeAnimal(animalId)
  if (vacunas.isPending || banos.isPending) {
    return <p className="text-[13.5px] text-hierro">Trayendo la sanidad…</p>
  }

  const hoy = new Date().toISOString().slice(0, 10)
  const registros = [
    ...(vacunas.data ?? []).map((v) => ({
      id: v.id,
      titulo: v.vacuna_nombre,
      fecha: v.fecha_aplicacion,
      vence: v.proxima_dosis_fecha,
      etiqueta: 'Vacuna',
      detalle: v.grupo_nombre ? `Por lote · ${v.grupo_nombre}` : 'Individual',
    })),
    ...(banos.data ?? []).map((b) => ({
      id: b.id,
      titulo: b.producto_nombre,
      fecha: b.fecha_bano,
      vence: b.proxima_fecha,
      etiqueta: 'Baño',
      detalle: b.carencia_carne_hasta
        ? `Carencia de carne hasta el ${fechaCorta(b.carencia_carne_hasta)}`
        : 'Sin carencia',
    })),
  ].sort((a, b) => (a.fecha < b.fecha ? 1 : -1))

  if (!registros.length) {
    return <Vacio>Sin vacunas ni baños registrados para este animal.</Vacio>
  }

  return (
    <Lista>
      {registros.map((registro) => {
        const vencido = registro.vence && registro.vence < hoy
        return (
          <Fila
            key={`${registro.etiqueta}-${registro.id}`}
            marca={vencido ? 'vencido' : registro.vence ? 'ok' : undefined}
            titulo={
              <>
                {registro.titulo}
                <Etiqueta>{registro.etiqueta}</Etiqueta>
              </>
            }
            meta={`${fechaCorta(registro.fecha)} · ${registro.detalle}`}
            derecha={
              registro.vence ? (
                <Etiqueta tono={vencido ? 'vencido' : 'ok'}>
                  {vencido ? 'Vencida' : fechaCorta(registro.vence)}
                </Etiqueta>
              ) : null
            }
          />
        )
      })}
    </Lista>
  )
}

function PanelRepro({ animalId, sexo }) {
  const hoja = useHojaReproductiva(animalId)

  if (sexo === 'macho') {
    return <Vacio>El ciclo reproductivo se lleva en las hembras.</Vacio>
  }
  if (hoja.isPending) return <p className="text-[13.5px] text-hierro">Trayendo el ciclo…</p>
  if (hoja.isError) return <Vacio>No pudimos traer el historial reproductivo.</Vacio>

  const datos = hoja.data
  if (!datos.eventos.length) {
    return <Vacio>Sin registros reproductivos. Empieza anotando un celo.</Vacio>
  }

  return (
    <>
      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-caja border border-borde bg-borde doble:grid-cols-4">
        <Dato rotulo="Estado">{datos.descripcion_estado}</Dato>
        <Dato rotulo="Partos">{datos.partos_totales}</Dato>
        <Dato rotulo="Intervalo entre partos">
          {datos.intervalo_promedio_dias ? `${datos.intervalo_promedio_dias} días` : null}
        </Dato>
        <Dato rotulo="Días abiertos">{datos.dias_abiertos}</Dato>
      </div>

      {datos.fecha_estimada_parto ? (
        <p className="mt-3 rounded-caja border border-[#C6E0D2] bg-[#F1F8F4] px-3.5 py-2.5 text-[13.5px] text-ok">
          Parto estimado el {fechaCorta(datos.fecha_estimada_parto)}.
        </p>
      ) : null}

      <div className="mt-3">
        <Lista>
          {[...datos.eventos].reverse().map((evento) => (
            <Fila
              key={`${evento.tipo}-${evento.referencia_id}`}
              titulo={evento.titulo}
              meta={evento.detalle}
              derecha={
                <span className="block text-[12.5px] text-hierro">{fechaCorta(evento.fecha)}</span>
              }
            />
          ))}
        </Lista>
      </div>
    </>
  )
}

function PanelGastos({ animalId }) {
  const { lista, resumen } = useGastosDeAnimal(animalId)
  if (lista.isPending) return <p className="text-[13.5px] text-hierro">Sumando los gastos…</p>

  const gastos = lista.data ?? []
  if (!gastos.length) {
    return <Vacio>Sin gastos cargados a este animal.</Vacio>
  }

  return (
    <Lista>
      {gastos.map((gasto) => (
        <Fila
          key={gasto.id}
          titulo={gasto.concepto}
          meta={`${gasto.categoria.replace('_', ' ')} · ${fechaCorta(gasto.fecha_gasto)}`}
          derecha={<b className="block text-[15px] peso-medio">$ {numero(gasto.monto, 2)}</b>}
        />
      ))}
      <Fila
        className="bg-[#FAFBF7]"
        titulo="Costo acumulado"
        meta="Desde el alta de la ficha"
        derecha={
          <b className="block text-[15px] peso-medio">$ {numero(resumen.data?.total ?? 0, 2)}</b>
        }
      />
    </Lista>
  )
}

export default function AnimalFicha({ id, conVolver = false }) {
  const navegar = useNavigate()
  const ficha = useAnimal(id)
  const arbol = useGenealogia(id)
  const [pestana, setPestana] = useState('resumen')
  const [accion, setAccion] = useState(null)

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
        <Dato rotulo="Lote">{animal.grupo_nombre}</Dato>
        <Dato rotulo="Potrero">{animal.potrero_nombre}</Dato>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <Boton variante="amarillo" chico onClick={() => setAccion('pesaje')}>
          Registrar pesaje
        </Boton>
        <Boton variante="suave" chico onClick={() => setAccion('vacuna')}>
          Vacuna
        </Boton>
        <Boton variante="suave" chico onClick={() => setAccion('gasto')}>
          Gasto
        </Boton>
      </div>

      <div
        role="tablist"
        className="-mx-3.5 mt-5 flex gap-0.5 overflow-x-auto border-b border-borde px-3.5 [scrollbar-width:none] rail:mx-0 rail:px-0"
      >
        {PESTANAS.map(([clave, texto]) => (
          <button
            key={clave}
            type="button"
            role="tab"
            aria-selected={pestana === clave}
            onClick={() => setPestana(clave)}
            className={`-mb-px flex-none whitespace-nowrap px-3 py-3 text-[14px] ${
              pestana === clave
                ? 'border-b-2 border-caravana text-tinta peso-medio'
                : 'border-b-2 border-transparent text-hierro'
            }`}
          >
            {texto}
          </button>
        ))}
      </div>

      <div className="pt-4">
        {pestana === 'resumen' && (
          <>
            {animal.observaciones ? (
              <p className="mb-3 rounded-caja border border-borde bg-superficie px-3.5 py-3 text-[14px]">
                {animal.observaciones}
              </p>
            ) : null}
            <div className="grid grid-cols-2 gap-2.5">
              <Pariente rotulo="Madre" nodo={raiz?.madre} />
              <Pariente rotulo="Padre" nodo={raiz?.padre} />
            </div>
            {raiz?.madre?.madre || raiz?.madre?.padre ? (
              <>
                <h3 className="mb-2.5 mt-3.5 text-[13px] text-hierro">Abuelos maternos</h3>
                <div className="grid grid-cols-2 gap-2.5">
                  <Pariente rotulo="Madre de la madre" nodo={raiz?.madre?.madre} />
                  <Pariente rotulo="Padre de la madre" nodo={raiz?.madre?.padre} />
                </div>
              </>
            ) : null}
          </>
        )}
        {pestana === 'peso' && <PanelPeso animalId={id} />}
        {pestana === 'sanidad' && <PanelSanidad animalId={id} />}
        {pestana === 'repro' && <PanelRepro animalId={id} sexo={animal.sexo} />}
        {pestana === 'gastos' && <PanelGastos animalId={id} />}
      </div>

      <FormaRegistro
        accion={accion}
        abierta={accion !== null}
        alCerrar={() => setAccion(null)}
        contexto={{ animal_id: id, __destino: 'animal' }}
      />
    </article>
  )
}
