/**
 * La chapa amarilla del arete. Es la identidad del animal y el unico elemento
 * de la interfaz que grita. No se usa para nada que no sea un arete.
 */
const TAMANOS = {
  chica: 'text-xs px-1.5 pt-0.5 pb-px border-b-2',
  normal: 'text-sm px-2 pt-[3px] pb-0.5 border-b-2',
  grande: 'text-[23px] px-3 pt-1.5 pb-1 border-b-[3px]',
}

export default function Caravana({ arete, tamano = 'normal', className = '' }) {
  return (
    <span
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-caravana border-b-caravanaSombra bg-caravana text-caravanaTinta ${TAMANOS[tamano]} ${className}`}
      style={{ fontVariationSettings: "'wdth' 85, 'wght' 800", letterSpacing: '0.01em' }}
    >
      {arete}
    </span>
  )
}
