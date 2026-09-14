import { Navigate, Route, Routes } from 'react-router-dom'

import Estructura from './armazon/Estructura'
import AnimalNuevo from './paginas/AnimalNuevo'
import Animales from './paginas/Animales'
import Potreros from './paginas/Potreros'
import Ingreso from './paginas/Ingreso'
import Proximamente from './paginas/Proximamente'
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
        <Route index element={<Navigate to="/animales" replace />} />
        <Route path="/animales" element={<Animales />} />
        <Route path="/animales/nuevo" element={<AnimalNuevo />} />
        <Route path="/animales/:id" element={<Animales />} />

        <Route
          path="/hoy"
          element={
            <Proximamente
              titulo="Hoy"
              explicacion="El resumen del día junta vencimientos, pesajes y lo registrado en el potrero. Llega cuando estén los módulos que lo alimentan."
            />
          }
        />
        <Route
          path="/alertas"
          element={
            <Proximamente
              titulo="Alertas"
              explicacion="Las alertas se calculan sobre vacunas, baños y partos. Llegan con esos módulos."
            />
          }
        />
        <Route path="/potreros" element={<Potreros />} />
        <Route
          path="/inventario"
          element={
            <Proximamente
              titulo="Inventario del hato"
              explicacion="El conteo por grupo, potrero, sexo y estado ya se calcula en el servidor. La pantalla llega enseguida."
            />
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/animales" replace />} />
    </Routes>
  )
}
