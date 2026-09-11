import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

import Boton from '../disenio/Boton'
import { IconoMas } from '../disenio/iconos'

/**
 * Hoja de registro rapido. Hoy abre con una sola opcion, porque hoy solo existe
 * el modulo de Animales. Va creciendo a medida que lleguen los demas.
 */
export default function HojaRegistro({ abierta, alCerrar }) {
  const navegar = useNavigate()

  useEffect(() => {
    if (!abierta) return
    const conTecla = (evento) => evento.key === 'Escape' && alCerrar()
    window.addEventListener('keydown', conTecla)
    return () => window.removeEventListener('keydown', conTecla)
  }, [abierta, alCerrar])

  if (!abierta) return null

  const irAlAlta = () => {
    alCerrar()
    navegar('/animales/nuevo')
  }

  return (
    <>
      <div className="fixed inset-0 z-50 bg-[#0C1611]/50" onClick={alCerrar} aria-hidden="true" />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-hoja"
        className="fixed inset-x-0 bottom-0 z-[51] max-h-[88dvh] overflow-auto rounded-t-2xl bg-papel px-3.5 pb-[calc(1.25rem+env(safe-area-inset-bottom,0))] pt-2 rail:inset-x-auto rail:bottom-auto rail:left-1/2 rail:top-1/2 rail:w-[640px] rail:-translate-x-1/2 rail:-translate-y-1/2 rail:rounded-caja rail:px-6 rail:pb-6 rail:pt-5"
      >
        <div className="mx-auto mb-3.5 mt-1.5 h-1 w-9 rounded-full bg-[#CBD3C6] rail:hidden" />
        <h2 id="titulo-hoja" className="mb-1 text-[19px] peso-titulo">
          Registrar en campo
        </h2>
        <p className="mb-3.5 text-[13.5px] text-hierro">
          Por ahora puedes dar de alta un animal. El resto llega con sus módulos.
        </p>

        <button
          type="button"
          onClick={irAlAlta}
          className="flex min-h-[66px] w-full items-center gap-3 rounded-caja border border-borde bg-superficie px-3.5 py-3.5 text-left hover:border-pastoClaro"
        >
          <IconoMas className="h-[22px] w-[22px] flex-none stroke-pasto" />
          <span className="text-[14.5px] peso-medio">
            Animal nuevo
            <i className="mt-px block text-xs font-normal not-italic text-hierro">Alta de ficha</i>
          </span>
        </button>

        <Boton variante="suave" bloque className="mt-3.5" onClick={alCerrar}>
          Cerrar
        </Boton>
      </div>
    </>
  )
}
