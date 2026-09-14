---
name: interfaz
description: Sistema de diseño de Hato — tokens de color, tipografia Archivo, los cinco componentes base, puntos de quiebre y voz de la interfaz. Usala antes de escribir cualquier pantalla o componente del frontend. Sustituye leer sources/maqueta-ganadera.html, que son 48 KB.
---

# Interfaz de Hato

**No abras `sources/maqueta-ganadera.html`.** Todo lo que necesitas esta aqui.

El ancla visual es la caravana: el arete se muestra siempre como una chapa
amarilla estampada, igual que la que el animal lleva en la oreja. Es el unico
elemento que grita. Todo lo demas es plano, de alto contraste, con bordes de un
pixel y sin sombras.

Quien lo usa trabaja en el potrero, a pleno sol, con una mano, con el telefono
sucio y sin señal. De ahi sale cada decision.

## Reglas duras

1. **Ningun hexadecimal suelto.** Los tokens estan en `tailwind.config.js`:
   `papel superficie tinta hierro borde pasto pastoClaro caravana
   caravanaSombra caravanaTinta vencido pronto ok sinEnviar`.
2. **Altura tactil minima 52 px** (`min-h-tap`) en todo lo que se toque.
3. **Los cinco componentes de `src/disenio/` estan cerrados**: Caravana, Fila,
   Etiqueta, Boton, Buscador. No se agregan mas sin decirlo.
4. **Sin sombras.** Bordes de 1 px y `rounded-caja` (10 px).
5. **Tres estados obligatorios** en toda pantalla con datos: cargando, error
   con boton de reintento, y lista vacia que invita a actuar.
6. **La interfaz no promete lo que no hace.** Nada de contadores falsos ni de
   «se guarda en el telefono» mientras no exista el outbox.

## Los tokens, y cuando se usan

```
papel       #F4F6F0   fondo de la aplicacion
superficie  #FFFFFF   tarjetas y listas
tinta       #121A15   texto principal
hierro      #66756B   texto secundario
borde       #DFE4D9   divisores
pasto       #0E3B2A   barra superior, rail, accion primaria
pastoClaro  #1C6647   foco y graficos
caravana    #FFC800   identidad del animal y boton de registro
vencido     #B22D1C   pasado de fecha
pronto      #B57200   vence esta semana
ok          #256F4E   al dia
sinEnviar   #3E6494   cambio pendiente de sincronizar
```

## Tipografia

Archivo variable. Los pesos se piden por eje con tres utilidades de
`estilos.css`, no con `font-bold`:

```
.peso-titulo   wdth 94, wght 700
.peso-fuerte   wdth 92, wght 720
.peso-medio    wght 620
```

Cifras tabulares activadas globalmente. No las desactives: sin ellas los pesos
bailan entre filas.

## Puntos de quiebre

```
< 900px    barra inferior de 5 posiciones, boton amarillo al centro
rail:      >= 900px   rail lateral de 224px, la barra inferior desaparece
doble:     >= 1100px  listado y ficha en dos paneles
```

En pantallas chicas la ficha ocupa toda la vista y lleva un «volver». En dos
paneles, no.

## Uso de los componentes

```jsx
<Caravana arete="C-0412" tamano="grande" />        // chica | normal | grande
<Etiqueta tono="pronto">Arete repetido</Etiqueta>  // neutro|vencido|pronto|ok|sinEnviar
<Boton variante="amarillo" bloque>Guardar ficha</Boton>  // primario|suave|amarillo|peligro
<Buscador valor={texto} alCambiar={setTexto} marcador="Buscar por arete o nombre" />

<Fila
  onClick={() => navegar(`/animales/${a.id}`)}
  marca="pronto"                                   // opcional: barra de color a la izquierda
  izquierda={<Caravana arete={a.arete} />}
  titulo={<>{a.nombre}<Etiqueta tono="pronto">Arete repetido</Etiqueta></>}
  meta="Brahman · 5 a 5 m · La Ceiba"
  derecha={<b className="peso-medio">472,0 kg</b>}
/>
```

Las filas van dentro de un contenedor con borde, separadas por `border-t`:

```jsx
<div className="overflow-hidden rounded-caja border border-borde bg-superficie">
  {filas.map((f, i) => (
    <div key={f.id} className={i ? 'border-t border-borde' : ''}>…</div>
  ))}
</div>
```

## Voz

Activa, frases cortas, sin mayusculas sostenidas, sin jerga. El usuario gestiona
animales, no entidades.

- Vacio: «Todavia no hay animales. Da de alta la primera ficha y empieza a
  llevar el hato.» + boton.
- Error: «No pudimos traer el hato» + el mensaje de la API + «Intentar otra vez».
- Sincronizacion: «3 sin enviar», «Al dia», «Sin señal». Nunca «sync pendiente».
- Formatos: coma decimal (`472,0 kg`), fechas cortas (`07 abr 2021`), edades en
  años y meses (`5 a 5 m`). Estan en `src/paginas/formato.js`.

## Trampas conocidas

- `h-5.5` **no existe** en Tailwind: la escala salta de 5 a 6. Usa `h-[22px]`.
- Un `<label>` no puede envolver un grupo de radios: tocar el rotulo selecciona
  el primero sin querer. Usa `fieldset` + `legend` (ver `Campo` en
  `AnimalNuevo.jsx`).
- El campo de busqueda va con fuente de 16 px o iOS hace zoom al enfocar.
- **Todo componente de formulario propio necesita `forwardRef`.** React Hook
  Form registra el campo pasando una ref al elemento del DOM; si el componente
  no la reenvia, el valor elegido nunca sale en el envio y **no hay ningun
  error**: el formulario guarda vacio. Le paso a `Desplegable` y solo se vio
  manejandolo en el navegador.
