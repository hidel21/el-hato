import { useNavigate } from 'react-router-dom'

import Boton from '../disenio/Boton'
import { IconoMas, IconoMovimiento } from '../disenio/iconos'
import Hoja from './Hoja'

/**
 * Hoja de registro rapido. Crece a medida que llegan los modulos: hoy solo
 * aparece lo que de verdad se puede registrar.
 */
const ACCIONES = [
  { texto: 'Animal nuevo', ayuda: 'Alta de ficha', a: '/animales/nuevo', Icono: IconoMas },
  {
    texto: 'Movimiento',
    ayuda: 'Cambio de potrero',
    a: '/potreros?mover=1',
    Icono: IconoMovimiento,
  },
]

export default function HojaRegistro({ abierta, alCerrar }) {
  const navegar = useNavigate()

  const ir = (a) => {
    alCerrar()
    navegar(a)
  }

  return (
    <Hoja
      abierta={abierta}
      alCerrar={alCerrar}
      titulo="Registrar en campo"
      descripcion="Esto es lo que ya puedes registrar. El resto llega con sus módulos."
    >
      <div className="grid grid-cols-2 gap-2.5">
        {ACCIONES.map(({ texto, ayuda, a, Icono }) => (
          <button
            key={a}
            type="button"
            onClick={() => ir(a)}
            className="flex min-h-[66px] items-center gap-3 rounded-caja border border-borde bg-superficie px-3.5 py-3.5 text-left hover:border-pastoClaro"
          >
            <Icono className="h-[22px] w-[22px] flex-none stroke-pasto" />
            <span className="text-[14.5px] peso-medio">
              {texto}
              <i className="mt-px block text-xs font-normal not-italic text-hierro">{ayuda}</i>
            </span>
          </button>
        ))}
      </div>

      <Boton variante="suave" bloque className="mt-3.5" onClick={alCerrar}>
        Cerrar
      </Boton>
    </Hoja>
  )
}
