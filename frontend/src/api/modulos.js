/**
 * Consultas de los modulos de dominio.
 *
 * Todo pasa por TanStack Query con la misma forma: un hook de listado, uno de
 * detalle cuando hace falta, y una mutacion que invalida lo que toco.
 */
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { LLAVE_ANIMALES } from './animales'
import { api } from './cliente'
import { LLAVE_LOTES, LLAVE_POTREROS } from './territorio'

export const LLAVE_PESAJES = ['pesajes']
export const LLAVE_VACUNACIONES = ['vacunaciones']
export const LLAVE_BANOS = ['banos']
export const LLAVE_CATALOGO_VACUNAS = ['catalogo-vacunas']
export const LLAVE_CATALOGO_PRODUCTOS = ['catalogo-productos']
export const LLAVE_REPRODUCCION = ['reproduccion']
export const LLAVE_GASTOS = ['gastos']
export const LLAVE_ALERTAS = ['alertas']
export const LLAVE_INVENTARIO = ['inventario']

// Una finca real no pasa de unos cientos de fichas activas. Para los
// selectores se traen de una vez en lugar de paginar dentro de una hoja.
const TODOS = 200

export function consulta(base, filtros = {}) {
  const parametros = new URLSearchParams()
  for (const [clave, valor] of Object.entries(filtros)) {
    if (valor !== undefined && valor !== null && valor !== '') parametros.set(clave, String(valor))
  }
  const cola = parametros.toString()
  return cola ? `${base}?${cola}` : base
}

function listaCompleta(llave, ruta, filtros = {}) {
  return {
    queryKey: [...llave, 'todos', filtros],
    queryFn: () => api.obtener(consulta(ruta, { ...filtros, limite: TODOS })),
    select: (pagina) => pagina.datos,
  }
}

// ---------- catalogos ----------

export const useCatalogoVacunas = () =>
  useQuery(listaCompleta(LLAVE_CATALOGO_VACUNAS, '/catalogo-vacunas', { solo_activas: true }))

export const useCatalogoProductos = () =>
  useQuery(
    listaCompleta(LLAVE_CATALOGO_PRODUCTOS, '/catalogo-productos-bano', {
      solo_activos: true,
    })
  )

// ---------- listados por animal, para la ficha ----------

export const useHistorialPeso = (animalId) =>
  useQuery({
    queryKey: [...LLAVE_PESAJES, 'animal', animalId],
    queryFn: () => api.obtener(`/pesajes/de-animal/${animalId}`),
    enabled: Boolean(animalId),
  })

export const useSanidadDeAnimal = (animalId) => ({
  vacunas: useQuery({
    queryKey: [...LLAVE_VACUNACIONES, 'animal', animalId],
    queryFn: () => api.obtener(consulta('/vacunaciones', { animal_id: animalId, limite: TODOS })),
    enabled: Boolean(animalId),
    select: (pagina) => pagina.datos,
  }),
  banos: useQuery({
    queryKey: [...LLAVE_BANOS, 'animal', animalId],
    queryFn: () => api.obtener(consulta('/banos', { animal_id: animalId, limite: TODOS })),
    enabled: Boolean(animalId),
    select: (pagina) => pagina.datos,
  }),
})

export const useHojaReproductiva = (animalId) =>
  useQuery({
    queryKey: [...LLAVE_REPRODUCCION, 'animal', animalId],
    queryFn: () => api.obtener(`/reproduccion/de-animal/${animalId}`),
    enabled: Boolean(animalId),
  })

export const useGastosDeAnimal = (animalId) => ({
  lista: useQuery({
    queryKey: [...LLAVE_GASTOS, 'animal', animalId],
    queryFn: () => api.obtener(consulta('/gastos', { animal_id: animalId, limite: TODOS })),
    enabled: Boolean(animalId),
    select: (pagina) => pagina.datos,
  }),
  resumen: useQuery({
    queryKey: [...LLAVE_GASTOS, 'resumen', animalId],
    queryFn: () => api.obtener(consulta('/gastos/resumen', { animal_id: animalId })),
    enabled: Boolean(animalId),
  }),
})

// ---------- listados de finca ----------

export const useInventario = () =>
  useQuery({
    queryKey: LLAVE_INVENTARIO,
    queryFn: () => api.obtener('/inventario'),
  })

export const useResumenGastos = (filtros = {}) =>
  useQuery({
    queryKey: [...LLAVE_GASTOS, 'resumen', filtros],
    queryFn: () => api.obtener(consulta('/gastos/resumen', filtros)),
  })

export const useGastos = (filtros = {}) =>
  useInfiniteQuery({
    queryKey: [...LLAVE_GASTOS, 'listado', filtros],
    queryFn: ({ pageParam }) =>
      api.obtener(consulta('/gastos', { ...filtros, limite: 25, cursor: pageParam })),
    initialPageParam: null,
    getNextPageParam: (ultima) => ultima.cursor_siguiente ?? undefined,
  })

/** Lo que hace falta para derivar las alertas en el dispositivo. */
export const useDatosParaAlertas = () => ({
  vacunaciones: useQuery(listaCompleta(LLAVE_VACUNACIONES, '/vacunaciones')),
  banos: useQuery(listaCompleta(LLAVE_BANOS, '/banos')),
  servicios: useQuery(listaCompleta(LLAVE_REPRODUCCION, '/reproduccion/servicios')),
  diagnosticos: useQuery(
    listaCompleta([...LLAVE_REPRODUCCION, 'dx'], '/reproduccion/diagnosticos', {
      resultado: 'prenada',
    })
  ),
  // Hacen falta para saber que gestaciones ya se cerraron.
  partos: useQuery(listaCompleta([...LLAVE_REPRODUCCION, 'partos'], '/reproduccion/partos')),
  guardadas: useQuery(listaCompleta(LLAVE_ALERTAS, '/alertas')),
})

export const usePesajesRecientes = (limite = 8) =>
  useQuery({
    queryKey: [...LLAVE_PESAJES, 'recientes', limite],
    queryFn: () => api.obtener(consulta('/pesajes', { limite })),
    select: (pagina) => pagina.datos,
  })

// ---------- mutaciones ----------

/** Tras registrar cualquier cosa cambia media aplicacion: se invalida todo. */
function invalidarTodo(clientes) {
  for (const llave of [
    LLAVE_ANIMALES,
    LLAVE_POTREROS,
    LLAVE_LOTES,
    LLAVE_PESAJES,
    LLAVE_VACUNACIONES,
    LLAVE_BANOS,
    LLAVE_REPRODUCCION,
    LLAVE_GASTOS,
    LLAVE_ALERTAS,
    LLAVE_INVENTARIO,
  ]) {
    clientes.invalidateQueries({ queryKey: llave })
  }
}

export function useRegistrar(ruta) {
  const clientes = useQueryClient()
  return useMutation({
    mutationFn: (datos) => api.crear(ruta, datos),
    onSuccess: () => invalidarTodo(clientes),
  })
}

export function useMarcarAlerta() {
  const clientes = useQueryClient()
  return useMutation({
    mutationFn: (datos) => api.crear('/alertas', datos),
    onSuccess: () => clientes.invalidateQueries({ queryKey: LLAVE_ALERTAS }),
  })
}

export function useCambiarAlerta() {
  const clientes = useQueryClient()
  return useMutation({
    mutationFn: ({ id, datos }) => api.editar(`/alertas/${id}`, datos),
    onSuccess: () => clientes.invalidateQueries({ queryKey: LLAVE_ALERTAS }),
  })
}
