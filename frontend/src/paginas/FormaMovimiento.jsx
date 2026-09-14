import { useState } from 'react'

import { useLotes, useMoverGanado, usePotreros } from '../api/territorio'
import Hoja from '../armazon/Hoja'
import Boton from '../disenio/Boton'
import { AvisoError, CLASE_CAMPO, Campo, Desplegable } from './campos'

const HOY = new Date().toISOString().slice(0, 10)

/**
 * Mover ganado de un potrero a otro.
 *
 * Solo se mueven lotes completos: mover un animal suelto lo permite la API,
 * pero en el potrero se arrea el lote entero, y una pantalla con menos
 * decisiones es una pantalla que se usa con una mano.
 */
export default function FormaMovimiento({ abierta, alCerrar, loteInicial = '' }) {
  const potreros = usePotreros()
  const lotes = useLotes()
  const mover = useMoverGanado()

  const [loteId, setLoteId] = useState(loteInicial)
  const [destinoId, setDestinoId] = useState('')
  const [fecha, setFecha] = useState(HOY)
  const [motivo, setMotivo] = useState('')
  const [errorApi, setErrorApi] = useState(null)

  const lote = (lotes.data ?? []).find((l) => l.id === loteId)
  const origen = lote?.potrero_nombre ?? null

  const cerrar = () => {
    setErrorApi(null)
    setDestinoId('')
    setMotivo('')
    alCerrar()
  }

  const enviar = async (evento) => {
    evento.preventDefault()
    setErrorApi(null)
    if (!loteId) return setErrorApi('Elige qué lote vas a mover.')
    if (!destinoId) return setErrorApi('Elige a qué potrero lo llevas.')

    try {
      await mover.mutateAsync({
        grupo_id: loteId,
        potrero_destino_id: destinoId,
        fecha_movimiento: fecha,
        motivo: motivo.trim() || undefined,
      })
      cerrar()
    } catch (error) {
      setErrorApi(error.message)
    }
  }

  const sinLotes = lotes.isSuccess && lotes.data.length === 0

  return (
    <Hoja
      abierta={abierta}
      alCerrar={cerrar}
      titulo="Mover ganado"
      descripcion="El lote entero cambia de potrero y queda el movimiento anotado."
    >
      {sinLotes ? (
        <div className="rounded-caja border border-borde bg-superficie px-4 py-8 text-center">
          <b className="mb-1 block text-[15.5px] peso-medio">Todavía no hay lotes</b>
          <p className="text-[13.5px] text-hierro">
            Arma un lote primero: es lo que se mueve de un potrero a otro.
          </p>
        </div>
      ) : (
        <form onSubmit={enviar} noValidate className="flex flex-col gap-3.5">
          <Campo
            rotulo="Qué lote"
            ayuda={
              lote
                ? `${lote.cantidad_animales} ${lote.cantidad_animales === 1 ? 'animal' : 'animales'}${origen ? ` · hoy en ${origen}` : ' · sin potrero'}`
                : 'Se mueven todos sus animales.'
            }
          >
            <Desplegable
              vacio="Elige un lote"
              value={loteId}
              onChange={(e) => setLoteId(e.target.value)}
              opciones={(lotes.data ?? []).map((l) => ({
                valor: l.id,
                texto: `${l.nombre} · ${l.cantidad_animales} animales`,
              }))}
            />
          </Campo>

          <Campo rotulo="A qué potrero">
            <Desplegable
              vacio="Elige el destino"
              value={destinoId}
              onChange={(e) => setDestinoId(e.target.value)}
              opciones={(potreros.data ?? [])
                .filter((p) => p.id !== lote?.potrero_id)
                .map((p) => ({
                  valor: p.id,
                  texto: p.en_descanso
                    ? `${p.nombre} · en descanso`
                    : `${p.nombre} · ${p.cantidad_animales} animales`,
                }))}
            />
          </Campo>

          <div className="grid grid-cols-2 gap-3">
            <Campo rotulo="Cuándo">
              <input
                type="date"
                max={HOY}
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                className={CLASE_CAMPO}
              />
            </Campo>
            <Campo rotulo="Por qué" ayuda="Opcional.">
              <input
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                placeholder="Rotación"
                autoComplete="off"
                className={CLASE_CAMPO}
              />
            </Campo>
          </div>

          <AvisoError mensaje={errorApi} />

          <div className="mt-1 flex flex-col gap-2 rail:flex-row-reverse">
            <Boton type="submit" variante="amarillo" bloque disabled={mover.isPending}>
              {mover.isPending ? 'Moviendo…' : 'Mover el lote'}
            </Boton>
            <Boton variante="suave" bloque onClick={cerrar}>
              Cancelar
            </Boton>
          </div>
        </form>
      )}
    </Hoja>
  )
}
