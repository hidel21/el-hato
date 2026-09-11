import { useCallback, useMemo, useState } from 'react'

import { borrarSesion, ingresar as pedirIngreso, leerSesion } from '../api/cliente'
import { ContextoSesion } from './contexto'

export function ProveedorSesion({ children }) {
  const [sesion, setSesion] = useState(() => leerSesion())

  const entrar = useCallback(async (correo, clave) => {
    const datos = await pedirIngreso(correo, clave)
    setSesion({ acceso: datos.token_acceso, usuario: datos.usuario })
    return datos.usuario
  }, [])

  const salir = useCallback(() => {
    borrarSesion()
    setSesion(null)
  }, [])

  const valor = useMemo(
    () => ({
      usuario: sesion?.usuario ?? null,
      autenticado: Boolean(sesion),
      entrar,
      salir,
    }),
    [sesion, entrar, salir]
  )

  return <ContextoSesion.Provider value={valor}>{children}</ContextoSesion.Provider>
}
