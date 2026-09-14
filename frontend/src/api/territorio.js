import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { LLAVE_ANIMALES } from './animales'
import { api } from './cliente'

export const LLAVE_POTREROS = ['potreros']
export const LLAVE_LOTES = ['lotes']
export const LLAVE_MOVIMIENTOS = ['movimientos']

function consulta(base, filtros = {}) {
  const parametros = new URLSearchParams()
  for (const [clave, valor] of Object.entries(filtros)) {
    if (valor !== undefined && valor !== null && valor !== '') parametros.set(clave, String(valor))
  }
  const cola = parametros.toString()
  return cola ? `${base}?${cola}` : base
}

// Una finca real no pasa de unas decenas de potreros o lotes, asi que para los
// selectores se traen todos de una vez en lugar de paginar.
const TODOS = 200

export function usePotreros() {
  return useQuery({
    queryKey: [...LLAVE_POTREROS, 'todos'],
    queryFn: () => api.obtener(consulta('/potreros', { limite: TODOS })),
    select: (pagina) => pagina.datos,
  })
}

export function useLotes(filtros = {}) {
  return useQuery({
    queryKey: [...LLAVE_LOTES, 'todos', filtros],
    queryFn: () => api.obtener(consulta('/grupos', { ...filtros, limite: TODOS })),
    select: (pagina) => pagina.datos,
  })
}

export function useMovimientos(filtros = {}) {
  return useInfiniteQuery({
    queryKey: [...LLAVE_MOVIMIENTOS, filtros],
    queryFn: ({ pageParam }) =>
      api.obtener(consulta('/potreros/movimientos', { ...filtros, limite: 20, cursor: pageParam })),
    initialPageParam: null,
    getNextPageParam: (ultima) => ultima.cursor_siguiente ?? undefined,
  })
}

/** Tras mover ganado cambian potreros, lotes y las fichas de los animales. */
function invalidarTodo(clientes) {
  clientes.invalidateQueries({ queryKey: LLAVE_POTREROS })
  clientes.invalidateQueries({ queryKey: LLAVE_LOTES })
  clientes.invalidateQueries({ queryKey: LLAVE_MOVIMIENTOS })
  clientes.invalidateQueries({ queryKey: LLAVE_ANIMALES })
}

export function useCrearPotrero() {
  const clientes = useQueryClient()
  return useMutation({
    mutationFn: (datos) => api.crear('/potreros', datos),
    onSuccess: () => clientes.invalidateQueries({ queryKey: LLAVE_POTREROS }),
  })
}

export function useActualizarPotrero() {
  const clientes = useQueryClient()
  return useMutation({
    mutationFn: ({ id, datos }) => api.editar(`/potreros/${id}`, datos),
    onSuccess: () => clientes.invalidateQueries({ queryKey: LLAVE_POTREROS }),
  })
}

export function useCrearLote() {
  const clientes = useQueryClient()
  return useMutation({
    mutationFn: (datos) => api.crear('/grupos', datos),
    onSuccess: () => {
      clientes.invalidateQueries({ queryKey: LLAVE_LOTES })
      clientes.invalidateQueries({ queryKey: LLAVE_POTREROS })
    },
  })
}

export function useMoverGanado() {
  const clientes = useQueryClient()
  return useMutation({
    mutationFn: (datos) => api.crear('/potreros/movimientos', datos),
    onSuccess: () => invalidarTodo(clientes),
  })
}
