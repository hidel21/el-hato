import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { useCrearAnimal } from '../api/animales'
import { useLotes, usePotreros } from '../api/territorio'
import Boton from '../disenio/Boton'
import Caravana from '../disenio/Caravana'
import { IconoVolver } from '../disenio/iconos'
import { AvisoError, CLASE_CAMPO, Campo, Desplegable } from './campos'

const HOY = new Date().toISOString().slice(0, 10)

const esquema = z.object({
  arete: z.string().trim().min(1, 'El arete es obligatorio').max(40, 'El arete es demasiado largo'),
  nombre: z.string().trim().max(120).optional().or(z.literal('')),
  sexo: z.enum(['hembra', 'macho'], { message: 'Elige hembra o macho' }),
  raza: z.string().trim().max(80).optional().or(z.literal('')),
  fecha_nacimiento: z
    .string()
    .optional()
    .or(z.literal(''))
    .refine((valor) => !valor || valor <= HOY, 'Esa fecha todavía no llega'),
  peso_actual_kg: z
    .string()
    .optional()
    .or(z.literal(''))
    .refine(
      (valor) => !valor || (Number(valor) > 0 && Number(valor) <= 2000),
      'Peso fuera de rango'
    ),
  grupo_id: z.string().optional().or(z.literal('')),
  potrero_id: z.string().optional().or(z.literal('')),
  observaciones: z.string().trim().max(600).optional().or(z.literal('')),
})

export default function AnimalNuevo() {
  const navegar = useNavigate()
  const crear = useCrearAnimal()
  const lotes = useLotes()
  const potreros = usePotreros()
  const [errorAlta, setErrorAlta] = useState(null)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(esquema),
    defaultValues: {
      arete: '',
      nombre: '',
      sexo: 'hembra',
      raza: '',
      fecha_nacimiento: '',
      peso_actual_kg: '',
      grupo_id: '',
      potrero_id: '',
      observaciones: '',
    },
  })

  const areteEscrito = watch('arete')

  // Al elegir el lote se propone su potrero: un animal que entra a un lote
  // entra al pasto donde ese lote esta. Se puede cambiar despues.
  const alElegirLote = (evento) => {
    const elegido = (lotes.data ?? []).find((l) => l.id === evento.target.value)
    if (elegido?.potrero_id) setValue('potrero_id', elegido.potrero_id)
  }

  const enviar = async (valores) => {
    setErrorAlta(null)
    const datos = {
      arete: valores.arete.trim().toUpperCase(),
      sexo: valores.sexo,
      nombre: valores.nombre || undefined,
      raza: valores.raza || undefined,
      fecha_nacimiento: valores.fecha_nacimiento || undefined,
      peso_actual_kg: valores.peso_actual_kg || undefined,
      grupo_id: valores.grupo_id || undefined,
      potrero_id: valores.potrero_id || undefined,
      observaciones: valores.observaciones || undefined,
    }
    try {
      const creado = await crear.mutateAsync(datos)
      navegar(`/animales/${creado.id}`, {
        replace: true,
        // Decision 1: el arete repetido se acepta y se avisa, no se rechaza.
        state: { avisoDuplicado: creado.arete_duplicado },
      })
    } catch (error) {
      setErrorAlta(error.message)
    }
  }

  return (
    <div className="mx-auto max-w-[560px]">
      <button
        type="button"
        onClick={() => navegar('/animales')}
        className="mb-1 flex items-center gap-1.5 py-2 text-[14px] text-hierro peso-medio"
      >
        <IconoVolver className="h-4 w-4 stroke-current" />
        Animales
      </button>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Caravana arete={areteEscrito?.toUpperCase() || '· · ·'} tamano="grande" />
        <div>
          <h1 className="text-[23px] peso-fuerte">Animal nuevo</h1>
          <p className="text-[13.5px] text-hierro">Con el arete basta. Lo demás puede esperar.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(enviar)} noValidate className="flex flex-col gap-3.5">
        <Campo rotulo="Arete" error={errors.arete?.message} ayuda="Como aparece en la oreja.">
          <input
            {...register('arete')}
            autoFocus
            autoCapitalize="characters"
            autoComplete="off"
            className={`${CLASE_CAMPO} uppercase`}
          />
        </Campo>

        <Campo rotulo="Sexo" grupo error={errors.sexo?.message}>
          <div className="grid grid-cols-2 gap-2">
            {['hembra', 'macho'].map((opcion) => (
              <label
                key={opcion}
                className="flex min-h-tap cursor-pointer items-center justify-center gap-2 rounded-caja border border-borde bg-superficie text-[15px] peso-medio has-[:checked]:border-pasto has-[:checked]:bg-pasto has-[:checked]:text-white"
              >
                <input type="radio" value={opcion} {...register('sexo')} className="sr-only" />
                {opcion === 'hembra' ? 'Hembra' : 'Macho'}
              </label>
            ))}
          </div>
        </Campo>

        <Campo rotulo="Nombre" error={errors.nombre?.message}>
          <input {...register('nombre')} autoComplete="off" className={CLASE_CAMPO} />
        </Campo>

        <Campo rotulo="Raza" error={errors.raza?.message}>
          <input {...register('raza')} autoComplete="off" className={CLASE_CAMPO} />
        </Campo>

        <div className="grid grid-cols-2 gap-3">
          <Campo rotulo="Nacimiento" error={errors.fecha_nacimiento?.message}>
            <input
              type="date"
              max={HOY}
              {...register('fecha_nacimiento')}
              className={CLASE_CAMPO}
            />
          </Campo>
          <Campo rotulo="Peso (kg)" error={errors.peso_actual_kg?.message}>
            <input
              type="number"
              step="0.5"
              inputMode="decimal"
              {...register('peso_actual_kg')}
              className={CLASE_CAMPO}
            />
          </Campo>
        </div>

        <Campo rotulo="Lote" ayuda="El grupo con el que se maneja.">
          <Desplegable
            opciones={(lotes.data ?? []).map((l) => ({
              valor: l.id,
              texto: `${l.nombre} · ${l.cantidad_animales} animales`,
            }))}
            {...register('grupo_id')}
            onChange={(evento) => {
              register('grupo_id').onChange(evento)
              alElegirLote(evento)
            }}
          />
        </Campo>

        <Campo rotulo="Potrero" ayuda="Dónde está pastando.">
          <Desplegable
            opciones={(potreros.data ?? []).map((p) => ({ valor: p.id, texto: p.nombre }))}
            {...register('potrero_id')}
          />
        </Campo>

        <Campo rotulo="Notas" error={errors.observaciones?.message}>
          <textarea
            rows={3}
            {...register('observaciones')}
            className={`${CLASE_CAMPO} py-2.5 leading-relaxed`}
          />
        </Campo>

        <AvisoError mensaje={errorAlta} />

        <div className="mt-1 flex flex-col gap-2 rail:flex-row-reverse">
          <Boton type="submit" variante="amarillo" bloque disabled={isSubmitting}>
            {isSubmitting ? 'Guardando…' : 'Guardar ficha'}
          </Boton>
          <Boton variante="suave" bloque onClick={() => navegar('/animales')}>
            Cancelar
          </Boton>
        </div>
      </form>
    </div>
  )
}
