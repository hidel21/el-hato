import { forwardRef } from 'react'

/**
 * Piezas de formulario. No son componentes del sistema de diseño —esos son
 * cinco y estan cerrados—, sino el andamio comun de las pantallas con campos.
 */

export const CLASE_CAMPO =
  'min-h-tap w-full rounded-caja border border-borde bg-superficie px-3 text-base outline-none focus:border-pastoClaro'

/**
 * Un campo con su rotulo. Con varios controles dentro (un grupo de radios) se
 * dibuja como fieldset: un <label> solo puede gobernar un control, y envolver
 * dos hace que tocar el rotulo seleccione el primero sin querer.
 */
export function Campo({ rotulo, ayuda, error, grupo = false, children }) {
  const pie = error ? (
    <span className="text-[13px] text-vencido">{error}</span>
  ) : ayuda ? (
    <span className="text-[12.5px] text-hierro">{ayuda}</span>
  ) : null

  if (grupo) {
    return (
      <fieldset className="flex flex-col gap-1.5 border-0 p-0">
        <legend className="mb-1.5 p-0 text-[13px] text-hierro">{rotulo}</legend>
        {children}
        {pie}
      </fieldset>
    )
  }

  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[13px] text-hierro">{rotulo}</span>
      {children}
      {pie}
    </label>
  )
}

/**
 * Desplegable. El vacio va primero para que se pueda dejar sin elegir.
 *
 * Va con forwardRef a proposito: React Hook Form registra el campo pasando una
 * ref al elemento del DOM. Sin reenviarla, el `register()` no llega al <select>
 * y el valor elegido nunca sale en el envio, sin ningun error a la vista.
 */
export const Desplegable = forwardRef(function Desplegable(
  { vacio = 'Sin asignar', opciones, ...resto },
  ref
) {
  return (
    <select ref={ref} className={CLASE_CAMPO} {...resto}>
      <option value="">{vacio}</option>
      {opciones.map(({ valor, texto }) => (
        <option key={valor} value={valor}>
          {texto}
        </option>
      ))}
    </select>
  )
})

/** Aviso de error de la API, con el mensaje tal como lo mando el servidor. */
export function AvisoError({ mensaje }) {
  if (!mensaje) return null
  return (
    <p className="rounded-caja border border-[#EDC7C1] bg-[#FDF3F1] px-3.5 py-2.5 text-[13.5px] text-vencido">
      {mensaje}
    </p>
  )
}
