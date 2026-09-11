# Sistema de diseño

El ancla visual es **la caravana**: el arete del animal se muestra siempre como
una chapa amarilla estampada, igual que la que el animal lleva en la oreja. Es
el unico elemento que grita. Todo lo demas es plano, de alto contraste, con
bordes de un pixel y sin sombras.

Quien lo usa trabaja en el potrero, a pleno sol, con una mano, con el telefono
sucio y sin señal la mayor parte del dia. Cada decision de aqui sale de ahi.

## Tokens

Estan en `frontend/tailwind.config.js` y se usan **por clase**, nunca en
hexadecimal suelto.

| Token | Valor | Para que |
|---|---|---|
| `papel` | `#F4F6F0` | fondo de la aplicacion |
| `superficie` | `#FFFFFF` | tarjetas y listas |
| `tinta` | `#121A15` | texto principal |
| `hierro` | `#66756B` | texto secundario |
| `borde` | `#DFE4D9` | divisores |
| `pasto` | `#0E3B2A` | barra superior, navegacion, accion primaria |
| `pastoClaro` | `#1C6647` | graficos, foco |
| `caravana` | `#FFC800` | identidad del animal y boton de registro |
| `caravanaSombra` | `#C99A00` | borde inferior de la chapa |
| `caravanaTinta` | `#241B00` | texto sobre amarillo |
| `vencido` | `#B22D1C` | pasado de fecha |
| `pronto` | `#B57200` | vence esta semana |
| `ok` | `#256F4E` | al dia |
| `sinEnviar` | `#3E6494` | cambio pendiente de sincronizar |

## Tipografia

**Archivo** variable, con los ejes `wght` y `wdth`. Los pesos se piden por eje,
no por clase de Tailwind; hay tres utilidades en `estilos.css`:

```
.peso-titulo   wdth 94, wght 700    titulos de pantalla
.peso-fuerte   wdth 92, wght 720    cifras grandes y encabezados
.peso-medio    wght 620             titulos de fila, botones, etiquetas
```

Las **cifras tabulares** estan activadas globalmente (`font-feature-settings:
'tnum' 1`). Sin eso, los pesos y las fechas bailan de una fila a otra y la
lista se vuelve ilegible de un vistazo.

## Medidas

```
radio de caja        10px   (rounded-caja)
radio de caravana     4px   (rounded-caravana) con borde inferior de 2px
altura tactil minima 52px   (min-h-tap) — nada por debajo
ancho del rail      224px
```

## Puntos de quiebre

```
< 900px    movil: barra inferior de cinco posiciones con boton amarillo central
>= 900px   rail:  el rail lateral de 224px reemplaza la barra inferior
>= 1100px  doble: listado y ficha en dos paneles simultaneos
```

En Tailwind son las pantallas `rail:` y `doble:`.

## Los cinco componentes

Estan en `frontend/src/disenio/` y **estan cerrados**: no se agregan mas sin
decirlo primero.

- **`Caravana`** — la chapa del arete. Tamaños `chica`, `normal`, `grande`. No
  se usa para nada que no sea un arete.
- **`Fila`** — el ladrillo de casi toda la aplicacion: marca de color opcional,
  algo a la izquierda (normalmente una caravana), titulo y meta en el centro,
  cifra a la derecha. Con `onClick` se vuelve un boton de 52 px de alto.
- **`Etiqueta`** — estado en una palabra. Tonos `neutro`, `vencido`, `pronto`,
  `ok`, `sinEnviar`.
- **`Boton`** — variantes `primario` (verde), `suave` (blanco), `amarillo`
  (registro) y `peligro`. La variante `chico` solo dentro de una fila, donde el
  objetivo tactil real es la fila entera.
- **`Buscador`** — campo de busqueda. La fuente es de 16 px porque por debajo
  de eso iOS hace zoom al enfocar.

## Voz de la interfaz

Activa, frases cortas, sin mayusculas sostenidas en las etiquetas, sin jerga
tecnica. **El usuario gestiona animales, no entidades.**

Los estados vacios invitan a actuar en vez de describir el sistema:

> **Todavia no hay animales**
> Da de alta la primera ficha y empieza a llevar el hato.
> [Dar de alta un animal]

El indicador de sincronizacion usa lenguaje de campo: «3 sin enviar», «Al dia»,
«Sin señal». Nunca «sync pendiente».

Y no promete lo que todavia no hace. Mientras no exista el outbox, el
indicador dice «Al dia» o «Sin señal» y nada mas: un contador de pendientes que
siempre marca cero es una mentira pequeña que se paga cara.

## Tres estados obligatorios

Toda pantalla que traiga datos resuelve **cargando**, **error** y **lista
vacia**. Una pantalla sin los tres no esta terminada. El error siempre trae un
boton para reintentar: en el potrero la señal va y viene.
