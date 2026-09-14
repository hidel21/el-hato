import { fechaCorta, numero } from './formato'

/**
 * Evolucion del peso. SVG a mano, sin libreria de graficas: son cinco o seis
 * puntos y una linea, y una dependencia de 300 KB para eso no se paga sola.
 */
export default function GraficaPeso({ pesajes }) {
  if (pesajes.length < 2) return null

  const pesos = pesajes.map((p) => Number(p.peso_kg))
  const minimo = Math.min(...pesos)
  const maximo = Math.max(...pesos)
  const rango = maximo - minimo || 1

  const ancho = 300
  const alto = 128
  const puntos = pesos.map((peso, indice) => [
    8 + indice * ((ancho - 16) / (pesos.length - 1)),
    108 - ((peso - minimo) / rango) * 88,
  ])

  const linea = puntos
    .map(([x, y], indice) => `${indice ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`)
    .join(' ')
  const area = `${linea} L${puntos.at(-1)[0].toFixed(1)} 120 L8 120 Z`

  const primero = pesajes[0]
  const ultimo = pesajes.at(-1)

  return (
    <div className="rounded-caja border border-borde bg-superficie p-3.5">
      <svg
        viewBox={`0 0 ${ancho} ${alto}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={`Evolución del peso, de ${numero(primero.peso_kg)} a ${numero(ultimo.peso_kg)} kilos`}
        className="block h-[132px] w-full overflow-visible"
      >
        <path d={area} fill="rgba(28,102,71,.10)" />
        <path
          d={linea}
          fill="none"
          stroke="#1C6647"
          strokeWidth="2.2"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {puntos.map(([x, y], indice) => (
          <circle
            key={indice}
            cx={x.toFixed(1)}
            cy={y.toFixed(1)}
            r={indice === puntos.length - 1 ? 4.5 : 3}
            fill={indice === puntos.length - 1 ? '#FFC800' : '#1C6647'}
            stroke="#fff"
            strokeWidth="1.6"
          />
        ))}
      </svg>

      <div className="mt-2.5 flex justify-between text-[13px] text-hierro">
        <span>
          {fechaCorta(primero.fecha_pesaje)} ·{' '}
          <b className="text-tinta peso-medio">{numero(primero.peso_kg)} kg</b>
        </span>
        <span>
          {fechaCorta(ultimo.fecha_pesaje)} ·{' '}
          <b className="text-tinta peso-medio">{numero(ultimo.peso_kg)} kg</b>
        </span>
      </div>
    </div>
  )
}
