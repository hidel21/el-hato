import { useNavigate } from 'react-router-dom'

import Boton from '../disenio/Boton'

/**
 * Seccion que todavia no tiene modulo. No es un relleno: dice la verdad de lo
 * que hay y lleva a lo que si se puede hacer hoy.
 */
export default function Proximamente({ titulo, explicacion }) {
  const navegar = useNavigate()

  return (
    <div>
      <h1 className="text-[26px] peso-fuerte">{titulo}</h1>
      <div className="mt-4 rounded-caja border border-borde bg-superficie px-4 py-10 text-center">
        <b className="mb-1 block text-[15.5px] peso-medio">Esta parte llega pronto</b>
        <p className="mx-auto mb-5 max-w-[340px] text-[13.5px] text-hierro">{explicacion}</p>
        <Boton variante="suave" onClick={() => navegar('/animales')}>
          Ir a los animales
        </Boton>
      </div>
    </div>
  )
}
