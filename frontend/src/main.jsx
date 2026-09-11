import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App'
import { ProveedorSesion } from './sesion/ContextoSesion'
import './estilos.css'

const clientes = new QueryClient({
  defaultOptions: {
    queries: {
      // En el potrero la señal va y viene: no vale la pena insistir mucho.
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
})

createRoot(document.getElementById('raiz')).render(
  <StrictMode>
    <QueryClientProvider client={clientes}>
      <BrowserRouter>
        <ProveedorSesion>
          <App />
        </ProveedorSesion>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>
)
