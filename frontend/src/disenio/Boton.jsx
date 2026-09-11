/**
 * Boton. Altura tactil de 52 px salvo en la variante chica, que solo se usa
 * dentro de una fila donde el objetivo real es la fila entera.
 */
const VARIANTES = {
  primario: 'bg-pasto text-white border-pasto',
  suave: 'bg-superficie text-tinta border-borde hover:border-pastoClaro',
  amarillo: 'bg-caravana text-caravanaTinta border-caravanaSombra border-b-2',
  peligro: 'bg-superficie text-vencido border-[#EDC7C1] hover:border-vencido',
}

export default function Boton({
  variante = 'primario',
  chico = false,
  bloque = false,
  type = 'button',
  children,
  className = '',
  ...resto
}) {
  const tamano = chico ? 'min-h-[36px] px-3 text-[13.5px]' : 'min-h-tap px-[18px] text-[15px]'
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded-lg border peso-medio transition-colors disabled:cursor-not-allowed disabled:opacity-55 ${VARIANTES[variante]} ${tamano} ${bloque ? 'w-full' : ''} ${className}`}
      {...resto}
    >
      {children}
    </button>
  )
}
