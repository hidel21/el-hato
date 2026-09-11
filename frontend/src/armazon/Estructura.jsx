import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'

import {
  IconoAlertas,
  IconoAnimales,
  IconoHoy,
  IconoInventario,
  IconoMarcaHato,
  IconoMas,
  IconoPotreros,
} from '../disenio/iconos'
import BarraSuperior from './BarraSuperior'
import HojaRegistro from './HojaRegistro'

const SECCIONES = [
  { a: '/hoy', texto: 'Hoy', Icono: IconoHoy, enBarra: true },
  { a: '/animales', texto: 'Animales', Icono: IconoAnimales, enBarra: true },
  { a: '/alertas', texto: 'Alertas', Icono: IconoAlertas, enBarra: true },
  { a: '/potreros', texto: 'Potreros', Icono: IconoPotreros, enBarra: true },
  { a: '/inventario', texto: 'Inventario', Icono: IconoInventario, enBarra: false },
]

export default function Estructura() {
  const [hojaAbierta, setHojaAbierta] = useState(false)
  const enBarra = SECCIONES.filter((seccion) => seccion.enBarra)

  return (
    <div className="flex min-h-dvh flex-col rail:flex-row">
      {/* Rail lateral desde 900 px */}
      <aside className="sticky top-0 hidden h-dvh w-rail flex-none flex-col gap-1 bg-pasto px-3 py-[18px] text-[#CFE0D5] rail:flex">
        <div className="flex items-center gap-2.5 px-2 pb-[18px] text-white">
          <IconoMarcaHato className="h-6 w-6 stroke-caravana" />
          <b className="text-[18px]" style={{ fontVariationSettings: "'wdth' 88, 'wght' 750" }}>
            Hato
          </b>
        </div>

        {SECCIONES.map(({ a, texto, Icono }) => (
          <NavLink
            key={a}
            to={a}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-[14.5px] ${
                isActive
                  ? 'bg-white/[.13] text-white peso-medio'
                  : 'text-[#BFD5C8] hover:bg-white/[.07] hover:text-white'
              }`
            }
          >
            <Icono className="h-[19px] w-[19px] flex-none stroke-current" />
            {texto}
          </NavLink>
        ))}

        <button
          type="button"
          onClick={() => setHojaAbierta(true)}
          className="mt-3 flex items-center justify-center gap-2 rounded-lg border-b-2 border-caravanaSombra bg-caravana px-3 py-2.5 text-[14.5px] text-caravanaTinta peso-medio"
        >
          <IconoMas className="h-[19px] w-[19px] stroke-caravanaTinta" />
          Registrar
        </button>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <BarraSuperior />
        <main className="mx-auto w-full max-w-[1180px] flex-1 px-3.5 pb-24 pt-4 rail:px-6 rail:pb-10 rail:pt-5">
          <Outlet />
        </main>
      </div>

      {/* Barra inferior hasta 900 px, con el boton amarillo al centro */}
      <nav
        aria-label="Secciones"
        className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 items-center border-t border-borde bg-superficie pb-[env(safe-area-inset-bottom,0)] rail:hidden"
      >
        {enBarra.slice(0, 2).map(({ a, texto, Icono }) => (
          <BotonBarra key={a} a={a} texto={texto} Icono={Icono} />
        ))}

        <button
          type="button"
          onClick={() => setHojaAbierta(true)}
          aria-label="Registrar"
          className="flex min-h-tap items-center justify-center py-2"
        >
          <span className="flex h-[46px] w-[46px] items-center justify-center rounded-[14px] border-b-2 border-caravanaSombra bg-caravana">
            <IconoMas className="h-6 w-6 stroke-caravanaTinta" />
          </span>
        </button>

        {enBarra.slice(2).map(({ a, texto, Icono }) => (
          <BotonBarra key={a} a={a} texto={texto} Icono={Icono} />
        ))}
      </nav>

      <HojaRegistro abierta={hojaAbierta} alCerrar={() => setHojaAbierta(false)} />
    </div>
  )
}

function BotonBarra({ a, texto, Icono }) {
  return (
    <NavLink
      to={a}
      className={({ isActive }) =>
        `flex min-h-[58px] flex-col items-center justify-center gap-[3px] px-0.5 py-2 text-[11px] peso-medio ${
          isActive ? 'text-pasto' : 'text-hierro'
        }`
      }
    >
      {({ isActive }) => (
        <>
          <Icono className={`h-[22px] w-[22px] stroke-current ${isActive ? 'stroke-[2.1]' : ''}`} />
          {texto}
        </>
      )}
    </NavLink>
  )
}
