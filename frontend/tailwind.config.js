/** Sistema de diseño de Hato.
 *
 * El ancla visual es la caravana: el arete se muestra siempre como una chapa
 * amarilla estampada, igual que la que el animal lleva en la oreja. Es el unico
 * elemento que grita. Todo lo demas es plano, de alto contraste, con bordes de
 * un pixel y sin sombras.
 */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        papel: '#F4F6F0', // fondo de la aplicacion
        superficie: '#FFFFFF', // tarjetas y listas
        tinta: '#121A15', // texto principal
        hierro: '#66756B', // texto secundario
        borde: '#DFE4D9', // divisores
        pasto: '#0E3B2A', // barra superior, navegacion, accion primaria
        pastoClaro: '#1C6647', // graficos, foco
        caravana: '#FFC800', // identidad del animal y boton de registro
        caravanaSombra: '#C99A00', // el borde inferior de la chapa
        caravanaTinta: '#241B00', // texto sobre amarillo
        vencido: '#B22D1C',
        pronto: '#B57200',
        ok: '#256F4E',
        sinEnviar: '#3E6494', // cambio pendiente de sincronizar
      },
      fontFamily: {
        sans: ['Archivo', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
      },
      borderRadius: {
        caja: '10px',
        caravana: '4px',
      },
      minHeight: {
        tap: '52px', // altura tactil minima. Nada por debajo.
      },
      spacing: {
        rail: '224px',
      },
      screens: {
        rail: '900px', // la barra inferior se cambia por el rail lateral
        doble: '1100px', // listado y ficha en dos paneles
      },
    },
  },
  plugins: [],
}
