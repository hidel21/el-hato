import { Navigate, useLocation } from 'react-router-dom'

import { useSesion } from './contexto'

export default function RutaProtegida({ children }) {
  const { autenticado } = useSesion()
  const ubicacion = useLocation()

  if (!autenticado) {
    return <Navigate to="/ingreso" state={{ desde: ubicacion.pathname }} replace />
  }
  return children
}
