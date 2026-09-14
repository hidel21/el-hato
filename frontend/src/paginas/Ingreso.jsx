import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import Boton from '../disenio/Boton'
import { IconoMarcaHato } from '../disenio/iconos'
import { useSesion } from '../sesion/contexto'

const esquema = z.object({
  correo: z.string().min(1, 'Escribe tu correo').email('Ese correo no parece válido'),
  clave: z.string().min(6, 'La clave tiene al menos 6 caracteres'),
})

export default function Ingreso() {
  const { autenticado, entrar } = useSesion()
  const navegar = useNavigate()
  const ubicacion = useLocation()
  const [errorEntrada, setErrorEntrada] = useState(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(esquema), defaultValues: { correo: '', clave: '' } })

  if (autenticado) return <Navigate to="/hoy" replace />

  const enviar = async ({ correo, clave }) => {
    setErrorEntrada(null)
    try {
      await entrar(correo, clave)
      navegar(ubicacion.state?.desde ?? '/hoy', { replace: true })
    } catch (error) {
      setErrorEntrada(error.message)
    }
  }

  return (
    <div className="flex min-h-dvh flex-col justify-center bg-papel px-4 py-10">
      <div className="mx-auto w-full max-w-[380px]">
        <div className="mb-6 flex items-center gap-2.5">
          <IconoMarcaHato className="h-8 w-8 stroke-pasto" />
          <b className="text-[26px] peso-fuerte">Hato</b>
        </div>

        <h1 className="mb-1 text-[22px] peso-titulo">Entra a tu finca</h1>
        <p className="mb-6 text-[13.5px] text-hierro">
          Usa el correo que te dio el administrador de la finca.
        </p>

        <form onSubmit={handleSubmit(enviar)} noValidate className="flex flex-col gap-3.5">
          <label className="flex flex-col gap-1.5">
            <span className="text-[13px] text-hierro">Correo</span>
            <input
              type="email"
              autoComplete="username"
              inputMode="email"
              {...register('correo')}
              className="min-h-tap rounded-caja border border-borde bg-superficie px-3 text-base outline-none focus:border-pastoClaro"
            />
            {errors.correo && (
              <span className="text-[13px] text-vencido">{errors.correo.message}</span>
            )}
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="text-[13px] text-hierro">Clave</span>
            <input
              type="password"
              autoComplete="current-password"
              {...register('clave')}
              className="min-h-tap rounded-caja border border-borde bg-superficie px-3 text-base outline-none focus:border-pastoClaro"
            />
            {errors.clave && (
              <span className="text-[13px] text-vencido">{errors.clave.message}</span>
            )}
          </label>

          {errorEntrada && (
            <p className="rounded-caja border border-[#EDC7C1] bg-[#FDF3F1] px-3 py-2.5 text-[13.5px] text-vencido">
              {errorEntrada}
            </p>
          )}

          <Boton type="submit" bloque disabled={isSubmitting} className="mt-1">
            {isSubmitting ? 'Entrando…' : 'Entrar'}
          </Boton>
        </form>
      </div>
    </div>
  )
}
