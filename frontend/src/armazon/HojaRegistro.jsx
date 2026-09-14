import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import Boton from '../disenio/Boton'
import {
  IconoBano,
  IconoCelo,
  IconoDiagnostico,
  IconoGasto,
  IconoMas,
  IconoMovimiento,
  IconoNacimiento,
  IconoPesaje,
  IconoServicio,
  IconoVacuna,
} from '../disenio/iconos'
import { ACCIONES, ORDEN_HOJA } from '../registro/definiciones'
import FormaRegistro from '../registro/FormaRegistro'
import { useSesion } from '../sesion/contexto'
import Hoja from './Hoja'

const ICONOS = {
  pesaje: IconoPesaje,
  vacuna: IconoVacuna,
  celo: IconoCelo,
  servicio: IconoServicio,
  bano: IconoBano,
  gasto: IconoGasto,
  diagnostico: IconoDiagnostico,
  nacimiento: IconoNacimiento,
}

/**
 * Lo que se puede registrar en el potrero, a un toque del boton amarillo.
 *
 * Cada opcion abre la misma hoja de formulario, dibujada desde la definicion
 * de esa accion. Las que el rol no puede hacer no se muestran.
 */
export default function HojaRegistro({ abierta, alCerrar }) {
  const navegar = useNavigate()
  const { usuario } = useSesion()
  const [accion, setAccion] = useState(null)
  const [aviso, setAviso] = useState(null)

  const permitida = (clave) => {
    const roles = ACCIONES[clave].soloRoles
    return !roles || roles.includes(usuario?.rol)
  }

  const ir = (a) => {
    alCerrar()
    navegar(a)
  }

  const abrirAccion = (clave) => {
    alCerrar()
    setAccion(clave)
  }

  const alGuardar = (definicion) => {
    setAviso(`${definicion.texto} guardado.`)
    setTimeout(() => setAviso(null), 2600)
  }

  return (
    <>
      <Hoja
        abierta={abierta}
        alCerrar={alCerrar}
        titulo="Registrar en campo"
        descripcion="Toca lo que acabas de hacer en el potrero."
      >
        <div className="grid grid-cols-2 gap-2.5 rail:grid-cols-3">
          {ORDEN_HOJA.filter(permitida).map((clave) => {
            const definicion = ACCIONES[clave]
            const Icono = ICONOS[definicion.icono]
            return (
              <button
                key={clave}
                type="button"
                onClick={() => abrirAccion(clave)}
                className="flex min-h-[66px] items-center gap-3 rounded-caja border border-borde bg-superficie px-3.5 py-3.5 text-left hover:border-pastoClaro"
              >
                <Icono className="h-[22px] w-[22px] flex-none stroke-pasto" />
                <span className="text-[14.5px] peso-medio">
                  {definicion.texto}
                  <i className="mt-px block text-xs font-normal not-italic text-hierro">
                    {definicion.ayuda}
                  </i>
                </span>
              </button>
            )
          })}

          <button
            type="button"
            onClick={() => ir('/potreros?mover=1')}
            className="flex min-h-[66px] items-center gap-3 rounded-caja border border-borde bg-superficie px-3.5 py-3.5 text-left hover:border-pastoClaro"
          >
            <IconoMovimiento className="h-[22px] w-[22px] flex-none stroke-pasto" />
            <span className="text-[14.5px] peso-medio">
              Movimiento
              <i className="mt-px block text-xs font-normal not-italic text-hierro">
                Cambio de potrero
              </i>
            </span>
          </button>

          <button
            type="button"
            onClick={() => ir('/animales/nuevo')}
            className="flex min-h-[66px] items-center gap-3 rounded-caja border border-borde bg-superficie px-3.5 py-3.5 text-left hover:border-pastoClaro"
          >
            <IconoMas className="h-[22px] w-[22px] flex-none stroke-pasto" />
            <span className="text-[14.5px] peso-medio">
              Animal nuevo
              <i className="mt-px block text-xs font-normal not-italic text-hierro">
                Alta de ficha
              </i>
            </span>
          </button>
        </div>

        <Boton variante="suave" bloque className="mt-3.5" onClick={alCerrar}>
          Cerrar
        </Boton>
      </Hoja>

      <FormaRegistro
        accion={accion}
        abierta={accion !== null}
        alCerrar={() => setAccion(null)}
        alGuardar={alGuardar}
      />

      {aviso ? (
        <div className="fixed inset-x-3.5 bottom-[78px] z-[60] flex items-center gap-2.5 rounded-caja bg-tinta px-3.5 py-3 text-[14px] text-[#F2F5F0] rail:inset-x-auto rail:bottom-6 rail:right-6 rail:max-w-[420px]">
          {aviso}
        </div>
      ) : null}
    </>
  )
}
