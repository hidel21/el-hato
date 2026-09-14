import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from './cliente'

export const LLAVE_ANIMALES = ['animales']

function armarConsulta({ buscar, estado, sexo, grupo_id, potrero_id, limite = 30, cursor }) {
  const parametros = new URLSearchParams()
  if (buscar?.trim()) parametros.set('buscar', buscar.trim())
  if (estado) parametros.set('estado', estado)
  if (sexo) parametros.set('sexo', sexo)
  if (grupo_id) parametros.set('grupo_id', grupo_id)
  if (potrero_id) parametros.set('potrero_id', potrero_id)
  parametros.set('limite', String(limite))
  if (cursor) parametros.set('cursor', cursor)
  return `/animales?${parametros.toString()}`
}

/** Listado paginado por cursor. La pagina siguiente se pide al llegar al final. */
export function useAnimales(filtros) {
  return useInfiniteQuery({
    queryKey: [...LLAVE_ANIMALES, 'listado', filtros],
    queryFn: ({ pageParam }) => api.obtener(armarConsulta({ ...filtros, cursor: pageParam })),
    initialPageParam: null,
    getNextPageParam: (ultima) => ultima.cursor_siguiente ?? undefined,
  })
}

export function useAnimal(id) {
  return useQuery({
    queryKey: [...LLAVE_ANIMALES, 'ficha', id],
    queryFn: () => api.obtener(`/animales/${id}`),
    enabled: Boolean(id),
  })
}

export function useGenealogia(id) {
  return useQuery({
    queryKey: [...LLAVE_ANIMALES, 'genealogia', id],
    queryFn: () => api.obtener(`/animales/${id}/genealogia`),
    enabled: Boolean(id),
  })
}

export function useCrearAnimal() {
  const clientes = useQueryClient()
  return useMutation({
    mutationFn: (datos) => api.crear('/animales', datos),
    onSuccess: () => clientes.invalidateQueries({ queryKey: LLAVE_ANIMALES }),
  })
}

/**
 * Lista plana de animales para los desplegables de las hojas de registro.
 * Una finca real no pasa de unos cientos de fichas activas.
 */
export function useAnimalesParaSelector(sexo) {
  return useQuery({
    queryKey: [...LLAVE_ANIMALES, 'selector', sexo ?? 'todos'],
    queryFn: () => api.obtener(armarConsulta({ sexo, limite: 200 })),
    select: (pagina) => pagina.datos,
  })
}
