/** Etiqueta de estado. Texto corto, sin mayusculas sostenidas. */
const TONOS = {
  neutro: 'bg-[#F7F9F4] text-hierro border-borde',
  vencido: 'bg-[#FDF3F1] text-vencido border-[#EDC7C1]',
  pronto: 'bg-[#FEF8EC] text-pronto border-[#EEDCBC]',
  ok: 'bg-[#F1F8F4] text-ok border-[#C6E0D2]',
  sinEnviar: 'bg-[#F2F6FB] text-sinEnviar border-[#C9D7E8]',
}

export default function Etiqueta({ tono = 'neutro', children, className = '' }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs peso-medio ${TONOS[tono]} ${className}`}
    >
      {children}
    </span>
  )
}
