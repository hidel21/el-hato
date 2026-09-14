import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// El proxy evita CORS en desarrollo: el navegador habla solo con Vite.
export default defineConfig({
  plugins: [react()],
  // Los archivos de prueba se llaman *.prueba.js, como todo lo demas aqui.
  test: {
    include: ['src/**/*.prueba.{js,jsx}'],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
