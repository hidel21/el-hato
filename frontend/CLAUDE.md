# Frontend

React 18 con **JavaScript, no TypeScript**. Vite, Tailwind, React Router,
TanStack Query, React Hook Form + Zod. Movil primero.

## Reglas que no se rompen

- **Ningun color en hexadecimal suelto.** Los doce tokens estan en
  `tailwind.config.js`: papel, superficie, tinta, hierro, borde, pasto,
  pastoClaro, caravana, vencido, pronto, ok, sinEnviar. Se usan por clase.
- **Altura tactil minima 52 px** en todo lo que se toque. Nada por debajo.
- **Los cinco componentes base de `src/disenio/` estan cerrados**: Caravana,
  Fila, Etiqueta, Boton, Buscador. No se agregan mas sin decirlo.
- Sin sombras. Bordes de un pixel. El unico elemento que grita es la caravana.
- **Voz de la interfaz**: activa, frases cortas, sin mayusculas sostenidas, sin
  jerga tecnica. El usuario gestiona animales, no entidades. Los estados vacios
  invitan a actuar. La sincronizacion se dice «3 sin enviar», «Al dia»,
  «Sin señal»; nunca «sync pendiente».
- Toda pantalla que traiga datos resuelve los tres estados: cargando, error y
  lista vacia. Una pantalla sin los tres no esta terminada.
- **Hay manifest pero NO hay service worker, y no se agrega hasta la Fase 2.**
  Mientras la interfaz lea de la red, cachear el shell solo consigue que la
  aplicacion abra sin señal para mostrar una lista vacia. Decision 21.

## Detalle de diseño

En la skill `interfaz` y en `docs/sistema-diseno.md`. No abras
`sources/maqueta-ganadera.html`: son 48 KB y ya esta destilada.
