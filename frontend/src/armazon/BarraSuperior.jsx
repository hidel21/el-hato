import { useSesion } from '../sesion/contexto'
import { IconoSalir } from '../disenio/iconos'
import { useConexion } from './useMedia'

const ROLES = {
  administrador: 'Administradora',
  veterinario: 'Veterinario',
  capataz: 'Capataz',
}

export default function BarraSuperior() {
  const { usuario, salir } = useSesion()
  const enLinea = useConexion()

  return (
    <>
      <header className="sticky top-0 z-40 bg-pasto px-3.5 pb-2.5 pt-[calc(0.625rem+env(safe-area-inset-top,0))] text-[#EDF3EE] rail:px-6 rail:py-3">
        <div className="flex items-center gap-2.5">
          <div className="flex min-w-0 flex-1 flex-col">
            <b className="truncate text-[15px]" style={{ fontVariationSettings: "'wght' 650" }}>
              {usuario?.finca_nombre ?? 'Sin finca'}
            </b>
            <span className="text-[12.5px] text-[#A9C4B4]">
              {usuario?.nombre_completo} · {ROLES[usuario?.rol] ?? usuario?.rol}
            </span>
          </div>

          <span
            className={`flex items-center gap-[7px] whitespace-nowrap rounded-full border px-2.5 py-[7px] text-[13px] peso-medio ${
              enLinea
                ? 'border-white/20 bg-white/10'
                : 'border-caravana/40 bg-caravana/15 text-caravana'
            }`}
          >
            <i
              className={`h-2 w-2 flex-none rounded-full ${enLinea ? 'bg-[#6FD39F]' : 'bg-caravana'}`}
            />
            {enLinea ? 'Al día' : 'Sin señal'}
          </span>

          <button
            type="button"
            onClick={salir}
            aria-label="Salir de la sesión"
            className="flex h-11 w-11 flex-none items-center justify-center rounded-lg hover:bg-white/10"
          >
            <IconoSalir className="h-5 w-5 stroke-current" />
          </button>
        </div>
      </header>

      {!enLinea && (
        <div className="bg-caravana px-3.5 py-[7px] text-[13px] text-[#3A2C00] peso-medio">
          Sin señal. Podrás seguir registrando cuando vuelva la conexión.
        </div>
      )}
    </>
  )
}
