/** Iconos de linea, 1.7 de grosor. Heredan el color de quien los contiene. */
const base = {
  viewBox: '0 0 24 24',
  fill: 'none',
  strokeWidth: 1.7,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

export function IconoLupa(props) {
  return (
    <svg {...base} strokeWidth={1.8} {...props}>
      <circle cx="11" cy="11" r="6.5" />
      <path d="m20 20-4.2-4.2" />
    </svg>
  )
}

export function IconoHoy(props) {
  return (
    <svg {...base} {...props}>
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5.5 10v9h13v-9" />
    </svg>
  )
}

export function IconoAnimales(props) {
  return (
    <svg {...base} {...props}>
      <path d="M4 6c0 3.5.8 5.4 2.6 6.4M19.4 6c0 3.5-.8 5.4-2.6 6.4" />
      <path d="M6.6 12.4c0 3.4 2.4 5.8 5.4 5.8s5.4-2.4 5.4-5.8" />
    </svg>
  )
}

export function IconoAlertas(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3a5.5 5.5 0 0 0-5.5 5.5c0 4-1.5 5.5-1.5 5.5h14s-1.5-1.5-1.5-5.5A5.5 5.5 0 0 0 12 3Z" />
      <path d="M10.2 18a2 2 0 0 0 3.6 0" />
    </svg>
  )
}

export function IconoPotreros(props) {
  return (
    <svg {...base} {...props}>
      <path d="M3 20V9l9-5 9 5v11" />
      <path d="M3 14h18M12 4v16" />
    </svg>
  )
}

export function IconoInventario(props) {
  return (
    <svg {...base} {...props}>
      <path d="M4 7h16v13H4z" />
      <path d="M4 11h16M9 7V4h6v3" />
    </svg>
  )
}

export function IconoMas(props) {
  return (
    <svg {...base} strokeWidth={2.2} {...props}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  )
}

export function IconoVolver(props) {
  return (
    <svg {...base} strokeWidth={2} {...props}>
      <path d="m14 6-6 6 6 6" />
    </svg>
  )
}

export function IconoSalir(props) {
  return (
    <svg {...base} {...props}>
      <path d="M15 17v2a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v2" />
      <path d="M19 12H9m10 0-3-3m3 3-3 3" />
    </svg>
  )
}

export function IconoMarcaHato(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth={1.8} strokeLinecap="round" {...props}>
      <path d="M4 5c0 4 1 6 3 7M20 5c0 4-1 6-3 7" />
      <path d="M7 12c0 3.5 2.2 6 5 6s5-2.5 5-6" />
      <circle cx="10" cy="13" r=".6" fill="currentColor" />
      <circle cx="14" cy="13" r=".6" fill="currentColor" />
    </svg>
  )
}
