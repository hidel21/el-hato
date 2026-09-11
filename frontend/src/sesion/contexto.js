import { createContext, useContext } from 'react'

export const ContextoSesion = createContext(null)

export function useSesion() {
  const valor = useContext(ContextoSesion)
  if (!valor) throw new Error('useSesion necesita estar dentro de ProveedorSesion')
  return valor
}
