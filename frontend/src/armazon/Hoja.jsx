import { useEffect } from 'react'

/**
 * La hoja que sube desde abajo en el telefono y se vuelve tarjeta centrada en
 * escritorio. Es el contenedor de todo lo que se registra sin salir de la
 * pantalla donde estas.
 */
export default function Hoja({ abierta, alCerrar, titulo, descripcion, children }) {
  useEffect(() => {
    if (!abierta) return
    const conTecla = (evento) => evento.key === 'Escape' && alCerrar()
    window.addEventListener('keydown', conTecla)
    return () => window.removeEventListener('keydown', conTecla)
  }, [abierta, alCerrar])

  if (!abierta) return null

  return (
    <>
      <div className="fixed inset-0 z-50 bg-[#0C1611]/50" onClick={alCerrar} aria-hidden="true" />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        className="fixed inset-x-0 bottom-0 z-[51] max-h-[88dvh] overflow-auto rounded-t-2xl bg-papel px-3.5 pb-[calc(1.25rem+env(safe-area-inset-bottom,0))] pt-2 rail:inset-x-auto rail:bottom-auto rail:left-1/2 rail:top-1/2 rail:w-[640px] rail:-translate-x-1/2 rail:-translate-y-1/2 rail:rounded-caja rail:px-6 rail:pb-6 rail:pt-5"
      >
        <div className="mx-auto mb-3.5 mt-1.5 h-1 w-9 rounded-full bg-[#CBD3C6] rail:hidden" />
        <h2 className="mb-1 text-[19px] peso-titulo">{titulo}</h2>
        {descripcion ? <p className="mb-3.5 text-[13.5px] text-hierro">{descripcion}</p> : null}
        {children}
      </div>
    </>
  )
}
