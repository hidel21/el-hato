import { Navigate, Route, Routes } from 'react-router-dom'

import Estructura from './armazon/Estructura'
import AnimalNuevo from './paginas/AnimalNuevo'
import Alertas from './paginas/Alertas'
import Animales from './paginas/Animales'
import Hoy from './paginas/Hoy'
import Inventario from './paginas/Inventario'
import Potreros from './paginas/Potreros'
import Ingreso from './paginas/Ingreso'
import RutaProtegida from './sesion/RutaProtegida'

export default function App() {
  return (
    <Routes>
      <Route path="/ingreso" element={<Ingreso />} />

      <Route
        element={
          <RutaProtegida>
            <Estructura />
          </RutaProtegida>
        }
      >
        <Route index element={<Navigate to="/hoy" replace />} />
        <Route path="/animales" element={<Animales />} />
        <Route path="/animales/nuevo" element={<AnimalNuevo />} />
        <Route path="/animales/:id" element={<Animales />} />

        <Route path="/hoy" element={<Hoy />} />
        <Route path="/alertas" element={<Alertas />} />
        <Route path="/potreros" element={<Potreros />} />
        <Route path="/inventario" element={<Inventario />} />
      </Route>

      <Route path="*" element={<Navigate to="/hoy" replace />} />
    </Routes>
  )
}
