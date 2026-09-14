import { describe, expect, it } from 'vitest'

import { contarPendientes, derivarAlertas } from './derivar'

// Fecha fija: las alertas dependen del calendario y las pruebas no deben.
const HOY = new Date(2026, 8, 14) // 14 de septiembre de 2026

const dia = (desplazamiento) => {
  const f = new Date(2026, 8, 14 + desplazamiento)
  return `${f.getFullYear()}-${String(f.getMonth() + 1).padStart(2, '0')}-${String(f.getDate()).padStart(2, '0')}`
}

describe('derivarAlertas', () => {
  it('reparte por urgencia segun cuantos dias faltan', () => {
    const grupos = derivarAlertas(
      {
        vacunaciones: [
          {
            id: 'v1',
            vacuna_nombre: 'Aftosa',
            cantidad_animales: 12,
            proxima_dosis_fecha: dia(-3),
          },
          { id: 'v2', vacuna_nombre: 'Carbón', cantidad_animales: 1, proxima_dosis_fecha: dia(4) },
          { id: 'v3', vacuna_nombre: 'Triple', cantidad_animales: 5, proxima_dosis_fecha: dia(40) },
        ],
      },
      HOY
    )

    expect(grupos.vencidas.map((a) => a.referencia_id)).toEqual(['v1'])
    expect(grupos.estaSemana.map((a) => a.referencia_id)).toEqual(['v2'])
    expect(grupos.proximas.map((a) => a.referencia_id)).toEqual(['v3'])
    expect(grupos.vencidas[0].titulo).toBe('12 refuerzos de Aftosa')
  })

  it('deja fuera lo que ya se atendio en cualquier dispositivo', () => {
    const datos = {
      banos: [
        {
          id: 'b1',
          producto_nombre: 'Garrapaticida',
          cantidad_animales: 34,
          proxima_fecha: dia(-2),
        },
      ],
    }
    expect(derivarAlertas(datos, HOY).vencidas).toHaveLength(1)

    const conMarca = {
      ...datos,
      guardadas: [{ estado: 'atendida', referencia_tabla: 'banos', referencia_id: 'b1' }],
    }
    expect(derivarAlertas(conMarca, HOY).vencidas).toHaveLength(0)
  })

  it('el diagnostico de preñez manda sobre el servicio', () => {
    const grupos = derivarAlertas(
      {
        servicios: [
          { id: 's1', animal_arete: 'C-0412', fecha_estimada_parto: dia(20), animal_id: 'a1' },
          { id: 's2', animal_arete: 'C-0503', fecha_estimada_parto: dia(30), animal_id: 'a2' },
        ],
        diagnosticos: [
          {
            id: 'd1',
            servicio_id: 's1',
            resultado: 'prenada',
            animal_arete: 'C-0412',
            animal_id: 'a1',
            fecha_estimada_parto: dia(18),
          },
        ],
      },
      HOY
    )

    const partos = grupos.proximas.filter((a) => a.tipo === 'parto')
    // El servicio ya palpado no genera alerta propia: la genera su diagnostico.
    expect(partos.map((a) => a.referencia_tabla)).toEqual([
      'diagnosticos_prenez',
      'servicios_reproductivos',
    ])
    expect(partos[1].titulo).toContain('sin diagnóstico')
  })

  it('una gestacion que ya termino en parto no sigue alertando', () => {
    const datos = {
      diagnosticos: [
        {
          id: 'd1',
          resultado: 'prenada',
          animal_id: 'a1',
          animal_arete: 'C-0188',
          fecha_diagnostico: dia(-300),
          fecha_estimada_parto: dia(-20),
        },
      ],
    }
    expect(derivarAlertas(datos, HOY).vencidas).toHaveLength(1)

    const yaPario = {
      ...datos,
      partos: [{ madre_id: 'a1', fecha_parto: dia(-25) }],
    }
    expect(derivarAlertas(yaPario, HOY).total).toBe(0)
  })

  it('un parto anterior al diagnostico no cierra la gestacion nueva', () => {
    const grupos = derivarAlertas(
      {
        diagnosticos: [
          {
            id: 'd1',
            resultado: 'prenada',
            animal_id: 'a1',
            animal_arete: 'C-0188',
            fecha_diagnostico: dia(-60),
            fecha_estimada_parto: dia(10),
          },
        ],
        partos: [{ madre_id: 'a1', fecha_parto: dia(-400) }],
      },
      HOY
    )

    expect(grupos.total).toBe(1)
  })

  it('avisa de rotacion solo cuando el potrero esta por pasarse', () => {
    const datos = (dias) => ({
      potreros: [
        {
          id: 'p1',
          nombre: 'La Ceiba',
          en_descanso: false,
          cantidad_animales: 68,
          dias_descanso_recomendado: 35,
          fecha_ultimo_ingreso: dia(-dias),
        },
      ],
    })

    expect(derivarAlertas(datos(10), HOY).total).toBe(0)
    expect(derivarAlertas(datos(41), HOY).vencidas[0].titulo).toBe('La Ceiba lleva 41 días ocupado')
    expect(derivarAlertas(datos(30), HOY).estaSemana).toHaveLength(1)
  })

  it('un potrero en descanso o vacio no pide rotacion', () => {
    const base = {
      id: 'p1',
      nombre: 'La Laguna',
      dias_descanso_recomendado: 30,
      fecha_ultimo_ingreso: dia(-90),
    }
    const enDescanso = { potreros: [{ ...base, en_descanso: true, cantidad_animales: 0 }] }
    const vacio = { potreros: [{ ...base, en_descanso: false, cantidad_animales: 0 }] }

    expect(derivarAlertas(enDescanso, HOY).total).toBe(0)
    expect(derivarAlertas(vacio, HOY).total).toBe(0)
  })

  it('no mira mas alla del horizonte', () => {
    const grupos = derivarAlertas(
      {
        vacunaciones: [
          {
            id: 'v1',
            vacuna_nombre: 'Aftosa',
            cantidad_animales: 1,
            proxima_dosis_fecha: dia(200),
          },
        ],
      },
      HOY
    )

    expect(grupos.total).toBe(0)
  })

  it('ordena de lo mas urgente a lo menos', () => {
    const grupos = derivarAlertas(
      {
        vacunaciones: [
          { id: 'v1', vacuna_nombre: 'A', cantidad_animales: 1, proxima_dosis_fecha: dia(5) },
          { id: 'v2', vacuna_nombre: 'B', cantidad_animales: 1, proxima_dosis_fecha: dia(-10) },
          { id: 'v3', vacuna_nombre: 'C', cantidad_animales: 1, proxima_dosis_fecha: dia(-1) },
        ],
      },
      HOY
    )

    expect(grupos.vencidas.map((a) => a.referencia_id)).toEqual(['v2', 'v3'])
  })

  it('cuenta como pendientes lo vencido y lo de esta semana', () => {
    const grupos = derivarAlertas(
      {
        vacunaciones: [
          { id: 'v1', vacuna_nombre: 'A', cantidad_animales: 1, proxima_dosis_fecha: dia(-1) },
          { id: 'v2', vacuna_nombre: 'B', cantidad_animales: 1, proxima_dosis_fecha: dia(3) },
          { id: 'v3', vacuna_nombre: 'C', cantidad_animales: 1, proxima_dosis_fecha: dia(60) },
        ],
      },
      HOY
    )

    expect(contarPendientes(grupos)).toBe(2)
  })

  it('sin datos devuelve grupos vacios y no revienta', () => {
    const grupos = derivarAlertas({}, HOY)

    expect(grupos).toEqual({ vencidas: [], estaSemana: [], proximas: [], total: 0 })
  })
})
