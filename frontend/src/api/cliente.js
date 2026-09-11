/**
 * Cliente HTTP de la API.
 *
 * Tres cosas y nada mas: pone el token, normaliza el error al formato de la API
 * y renueva la sesion una sola vez cuando el token de acceso vence.
 */
const BASE = import.meta.env.VITE_API_URL ?? '/api/v1'

const LLAVE_ACCESO = 'hato.token_acceso'
const LLAVE_REFRESCO = 'hato.token_refresco'
const LLAVE_USUARIO = 'hato.usuario'

export function leerSesion() {
  const acceso = localStorage.getItem(LLAVE_ACCESO)
  const usuarioCrudo = localStorage.getItem(LLAVE_USUARIO)
  if (!acceso || !usuarioCrudo) return null
  try {
    return { acceso, usuario: JSON.parse(usuarioCrudo) }
  } catch {
    return null
  }
}

export function guardarSesion(respuesta) {
  localStorage.setItem(LLAVE_ACCESO, respuesta.token_acceso)
  localStorage.setItem(LLAVE_REFRESCO, respuesta.token_refresco)
  localStorage.setItem(LLAVE_USUARIO, JSON.stringify(respuesta.usuario))
}

export function borrarSesion() {
  localStorage.removeItem(LLAVE_ACCESO)
  localStorage.removeItem(LLAVE_REFRESCO)
  localStorage.removeItem(LLAVE_USUARIO)
}

/** Error con el codigo que devolvio la API, para poder decidir sobre el. */
export class ErrorAPI extends Error {
  constructor(codigo, mensaje, estado) {
    super(mensaje)
    this.codigo = codigo
    this.estado = estado
  }
}

const SIN_CONEXION = 'No hay conexion con el servidor. Revisa la señal e intenta otra vez.'

async function aError(respuesta) {
  let cuerpo = null
  try {
    cuerpo = await respuesta.json()
  } catch {
    cuerpo = null
  }
  const error = cuerpo?.error
  return new ErrorAPI(
    error?.code ?? 'error',
    error?.message ?? 'Algo fallo. Intenta otra vez.',
    respuesta.status
  )
}

async function renovarSesion() {
  const refresco = localStorage.getItem(LLAVE_REFRESCO)
  if (!refresco) return false

  const respuesta = await fetch(`${BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token_refresco: refresco }),
  })
  if (!respuesta.ok) {
    borrarSesion()
    return false
  }
  guardarSesion(await respuesta.json())
  return true
}

async function enviar(ruta, opciones, reintentar) {
  const acceso = localStorage.getItem(LLAVE_ACCESO)
  const cabeceras = { ...(opciones.headers ?? {}) }
  if (opciones.body) cabeceras['Content-Type'] = 'application/json'
  if (acceso) cabeceras.Authorization = `Bearer ${acceso}`

  let respuesta
  try {
    respuesta = await fetch(`${BASE}${ruta}`, { ...opciones, headers: cabeceras })
  } catch {
    throw new ErrorAPI('sin_conexion', SIN_CONEXION, 0)
  }

  if (respuesta.status === 401 && reintentar && (await renovarSesion())) {
    return enviar(ruta, opciones, false)
  }
  if (!respuesta.ok) throw await aError(respuesta)
  if (respuesta.status === 204) return null
  return respuesta.json()
}

export const api = {
  obtener: (ruta) => enviar(ruta, { method: 'GET' }, true),
  crear: (ruta, datos) => enviar(ruta, { method: 'POST', body: JSON.stringify(datos) }, true),
  editar: (ruta, datos) => enviar(ruta, { method: 'PUT', body: JSON.stringify(datos) }, true),
  borrar: (ruta) => enviar(ruta, { method: 'DELETE' }, true),
}

/** El ingreso va aparte: no lleva token ni debe reintentar. */
export async function ingresar(correo, clave) {
  let respuesta
  try {
    respuesta = await fetch(`${BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ correo, clave }),
    })
  } catch {
    throw new ErrorAPI('sin_conexion', SIN_CONEXION, 0)
  }
  if (!respuesta.ok) throw await aError(respuesta)

  const datos = await respuesta.json()
  guardarSesion(datos)
  return datos
}
