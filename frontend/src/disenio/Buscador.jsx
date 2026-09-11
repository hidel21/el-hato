import { IconoLupa } from './iconos'

/** Campo de busqueda. 16 px de fuente: por debajo, iOS hace zoom al enfocar. */
export default function Buscador({ valor, alCambiar, marcador = 'Buscar', ...resto }) {
  return (
    <div className="flex min-h-tap items-center gap-2.5 rounded-caja border border-borde bg-superficie px-3 focus-within:border-pastoClaro">
      <IconoLupa className="h-[19px] w-[19px] flex-none stroke-hierro" />
      <input
        type="search"
        value={valor}
        onChange={(evento) => alCambiar(evento.target.value)}
        placeholder={marcador}
        autoComplete="off"
        className="min-w-0 flex-1 border-none bg-transparent py-3.5 text-base outline-none placeholder:text-hierro"
        {...resto}
      />
    </div>
  )
}
