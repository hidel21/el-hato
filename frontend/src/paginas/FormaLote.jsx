import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { useCrearLote, usePotreros } from '../api/territorio'
import Hoja from '../armazon/Hoja'
import Boton from '../disenio/Boton'
import { AvisoError, CLASE_CAMPO, Campo, Desplegable } from './campos'
import { ETAPAS, PROPOSITOS } from './formato'

const esquema = z.object({
  nombre: z.string().trim().min(1, 'Ponle un nombre').max(120),
  etapa: z.string().min(1, 'Elige la etapa'),
  proposito: z.string().min(1, 'Elige el propósito'),
  potrero_id: z.string().optional().or(z.literal('')),
  descripcion: z.string().trim().max(600).optional().or(z.literal('')),
})

export default function FormaLote({ abierta, alCerrar }) {
  const crear = useCrearLote()
  const potreros = usePotreros()
  const [errorApi, setErrorApi] = useState(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(esquema),
    defaultValues: {
      nombre: '',
      etapa: 'levante',
      proposito: 'engorde',
      potrero_id: '',
      descripcion: '',
    },
  })

  const cerrar = () => {
    setErrorApi(null)
    reset()
    alCerrar()
  }

  const enviar = async (valores) => {
    setErrorApi(null)
    try {
      await crear.mutateAsync({
        nombre: valores.nombre.trim(),
        etapa: valores.etapa,
        proposito: valores.proposito,
        potrero_id: valores.potrero_id || undefined,
        descripcion: valores.descripcion || undefined,
      })
      cerrar()
    } catch (error) {
      setErrorApi(error.message)
    }
  }

  return (
    <Hoja
      abierta={abierta}
      alCerrar={cerrar}
      titulo="Lote nuevo"
      descripcion="Un lote es el grupo de animales que se maneja junto."
    >
      <form onSubmit={handleSubmit(enviar)} noValidate className="flex flex-col gap-3.5">
        <Campo rotulo="Nombre" ayuda="Como lo llaman en la finca." error={errors.nombre?.message}>
          <input {...register('nombre')} autoComplete="off" className={CLASE_CAMPO} />
        </Campo>

        <div className="grid grid-cols-2 gap-3">
          <Campo rotulo="Etapa" error={errors.etapa?.message}>
            <Desplegable
              vacio="Elige una"
              opciones={ETAPAS.map(([valor, texto]) => ({ valor, texto }))}
              {...register('etapa')}
            />
          </Campo>
          <Campo rotulo="Propósito" error={errors.proposito?.message}>
            <Desplegable
              vacio="Elige uno"
              opciones={PROPOSITOS.map(([valor, texto]) => ({ valor, texto }))}
              {...register('proposito')}
            />
          </Campo>
        </div>

        <Campo rotulo="Potrero" ayuda="Dónde está pastando ahora.">
          <Desplegable
            opciones={(potreros.data ?? []).map((p) => ({ valor: p.id, texto: p.nombre }))}
            {...register('potrero_id')}
          />
        </Campo>

        <Campo rotulo="Notas" error={errors.descripcion?.message}>
          <textarea
            rows={2}
            {...register('descripcion')}
            className={`${CLASE_CAMPO} py-2.5 leading-relaxed`}
          />
        </Campo>

        <AvisoError mensaje={errorApi} />

        <div className="mt-1 flex flex-col gap-2 rail:flex-row-reverse">
          <Boton type="submit" variante="amarillo" bloque disabled={isSubmitting}>
            {isSubmitting ? 'Guardando…' : 'Crear lote'}
          </Boton>
          <Boton variante="suave" bloque onClick={cerrar}>
            Cancelar
          </Boton>
        </div>
      </form>
    </Hoja>
  )
}
