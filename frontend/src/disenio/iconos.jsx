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

export function IconoMovimiento(props) {
  return (
    <svg {...base} {...props}>
      <path d="M4 8h13l-3-3M20 16H7l3 3" />
    </svg>
  )
}

export function IconoPesaje(props) {
  return (
    <svg {...base} {...props}>
      <path d="M4 20h16L18 7H6L4 20Z" />
      <path d="M12 7V4" />
      <path d="M9 12.5 12 16l4-6" />
    </svg>
  )
}

export function IconoVacuna(props) {
  return (
    <svg {...base} {...props}>
      <path d="m15 4 5 5M17.5 6.5 9 15l-3 1 1-3 8.5-8.5" />
      <path d="m4 20 2-2" />
    </svg>
  )
}

export function IconoCelo(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="9" r="5" />
      <path d="M12 14v7M9 18h6" />
    </svg>
  )
}

export function IconoServicio(props) {
  return (
    <svg {...base} {...props}>
      <path d="M8 4v6a4 4 0 0 0 8 0V4" />
      <path d="M12 14v6M9 20h6" />
    </svg>
  )
}

export function IconoBano(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3c3 4 5 6.2 5 9a5 5 0 0 1-10 0c0-2.8 2-5 5-9Z" />
    </svg>
  )
}

export function IconoGasto(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 4v16" />
      <path d="M15.5 7.5H10a2.5 2.5 0 0 0 0 5h4a2.5 2.5 0 0 1 0 5H8" />
    </svg>
  )
}

export function IconoDiagnostico(props) {
  return (
    <svg {...base} {...props}>
      <path d="M6 3v6a6 6 0 0 0 12 0V3" />
      <circle cx="12" cy="15" r="3" />
      <path d="M12 18v3" />
    </svg>
  )
}

export function IconoNacimiento(props) {
  return (
    <svg {...base} {...props}>
      <path d="M7 18c0-3 2.2-5 5-5s5 2 5 5" />
      <circle cx="12" cy="8" r="3" />
    </svg>
  )
}
