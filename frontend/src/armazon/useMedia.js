import { useEffect, useState } from 'react'

/** Escucha una media query. Se usa para decidir entre un panel y dos. */
export function useMedia(consulta) {
  const [coincide, setCoincide] = useState(
    () => typeof window !== 'undefined' && window.matchMedia(consulta).matches
  )

  useEffect(() => {
    const lista = window.matchMedia(consulta)
    const alCambiar = (evento) => setCoincide(evento.matches)
    setCoincide(lista.matches)
    lista.addEventListener('change', alCambiar)
    return () => lista.removeEventListener('change', alCambiar)
  }, [consulta])

  return coincide
}

/** True cuando el navegador cree tener conexion. */
export function useConexion() {
  const [enLinea, setEnLinea] = useState(() => navigator.onLine)

  useEffect(() => {
    const conectar = () => setEnLinea(true)
    const desconectar = () => setEnLinea(false)
    window.addEventListener('online', conectar)
    window.addEventListener('offline', desconectar)
    return () => {
      window.removeEventListener('online', conectar)
      window.removeEventListener('offline', desconectar)
    }
  }, [])

  return enLinea
}
