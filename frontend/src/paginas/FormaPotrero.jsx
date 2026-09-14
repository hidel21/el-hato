import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { useActualizarPotrero, useCrearPotrero } from '../api/territorio'
import Hoja from '../armazon/Hoja'
import Boton from '../disenio/Boton'
import { AvisoError, CLASE_CAMPO, Campo, Desplegable } from './campos'
import { PASTOS } from './formato'

const esquema = z.object({
  nombre: z.string().trim().min(1, 'Ponle un nombre').max(120),
  hectareas: z
    .string()
    .min(1, 'Cuántas hectáreas tiene')
    .refine((v) => Number(v) > 0, 'Tienen que ser más de cero'),
  tipo_pasto: z.string().optional().or(z.literal('')),
  capacidad_ugm_ha: z
    .string()
    .optional()
    .or(z.literal(''))
    .refine((v) => !v || (Number(v) > 0 && Number(v) <= 20), 'Entre 0 y 20'),
  dias_descanso_recomendado: z
    .string()
    .optional()
    .or(z.literal(''))
    .refine((v) => !v || (Number(v) >= 1 && Number(v) <= 365), 'Entre 1 y 365 días'),
  observaciones: z.string().trim().max(600).optional().or(z.literal('')),
})

export default function FormaPotrero({ abierta, alCerrar, potrero = null }) {
  const crear = useCrearPotrero()
  const actualizar = useActualizarPotrero()
  const [errorApi, setErrorApi] = useState(null)
  const editando = Boolean(potrero)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(esquema),
    values: {
      nombre: potrero?.nombre ?? '',
      hectareas: potrero ? String(Number(potrero.hectareas)) : '',
      tipo_pasto: potrero?.tipo_pasto ?? '',
      capacidad_ugm_ha: potrero?.capacidad_ugm_ha ? String(Number(potrero.capacidad_ugm_ha)) : '',
      dias_descanso_recomendado: String(potrero?.dias_descanso_recomendado ?? 30),
      observaciones: potrero?.observaciones ?? '',
    },
  })

  const cerrar = () => {
    setErrorApi(null)
    reset()
    alCerrar()
  }

  const enviar = async (valores) => {
    setErrorApi(null)
    const datos = {
      nombre: valores.nombre.trim(),
      hectareas: valores.hectareas,
      tipo_pasto: valores.tipo_pasto || undefined,
      capacidad_ugm_ha: valores.capacidad_ugm_ha || undefined,
      dias_descanso_recomendado: Number(valores.dias_descanso_recomendado || 30),
      observaciones: valores.observaciones || undefined,
    }
    try {
      if (editando) await actualizar.mutateAsync({ id: potrero.id, datos })
      else await crear.mutateAsync(datos)
      cerrar()
    } catch (error) {
      setErrorApi(error.message)
    }
  }

  return (
    <Hoja
      abierta={abierta}
      alCerrar={cerrar}
      titulo={editando ? `Editar ${potrero.nombre}` : 'Potrero nuevo'}
      descripcion="Con el nombre y las hectáreas basta para empezar."
    >
      <form onSubmit={handleSubmit(enviar)} noValidate className="flex flex-col gap-3.5">
        <Campo rotulo="Nombre" error={errors.nombre?.message}>
          <input {...register('nombre')} autoComplete="off" className={CLASE_CAMPO} />
        </Campo>

        <div className="grid grid-cols-2 gap-3">
          <Campo rotulo="Hectáreas" error={errors.hectareas?.message}>
            <input
              type="number"
              step="0.5"
              inputMode="decimal"
              {...register('hectareas')}
              className={CLASE_CAMPO}
            />
          </Campo>
          <Campo
            rotulo="Capacidad"
            ayuda="UGM por hectárea"
            error={errors.capacidad_ugm_ha?.message}
          >
            <input
              type="number"
              step="0.1"
              inputMode="decimal"
              {...register('capacidad_ugm_ha')}
              className={CLASE_CAMPO}
            />
          </Campo>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Campo rotulo="Pasto" error={errors.tipo_pasto?.message}>
            <Desplegable
              vacio="Sin registrar"
              opciones={PASTOS.map(([valor, texto]) => ({ valor, texto }))}
              {...register('tipo_pasto')}
            />
          </Campo>
          <Campo
            rotulo="Descanso"
            ayuda="Días recomendados"
            error={errors.dias_descanso_recomendado?.message}
          >
            <input
              type="number"
              inputMode="numeric"
              {...register('dias_descanso_recomendado')}
              className={CLASE_CAMPO}
            />
          </Campo>
        </div>

        <Campo rotulo="Notas" error={errors.observaciones?.message}>
          <textarea
            rows={2}
            {...register('observaciones')}
            className={`${CLASE_CAMPO} py-2.5 leading-relaxed`}
          />
        </Campo>

        <AvisoError mensaje={errorApi} />

        <div className="mt-1 flex flex-col gap-2 rail:flex-row-reverse">
          <Boton type="submit" variante="amarillo" bloque disabled={isSubmitting}>
            {isSubmitting ? 'Guardando…' : editando ? 'Guardar cambios' : 'Crear potrero'}
          </Boton>
          <Boton variante="suave" bloque onClick={cerrar}>
            Cancelar
          </Boton>
        </div>
      </form>
    </Hoja>
  )
}
