# Contrato de sincronizacion

Esto **no esta construido**. Se escribe hoy, con las decisiones frescas, para
que la Fase 2 no tenga que reconstruir el razonamiento. Todo lo que se menciona
como «ya existe» esta en la base desde la migracion inicial.

## El problema

El capataz trabaja sin señal la mayor parte del dia. La aplicacion final sera
una PWA offline-first donde **IndexedDB es la unica fuente de datos de la
interfaz**: la pantalla nunca lee de la red. Lo que se escribe en el potrero se
guarda en el dispositivo y sale despues, cuando haya señal.

## Piezas ya construidas

### Columnas de sincronizacion

Cada tabla sincronizable ya lleva `device_id`, `version`, `client_timestamp` y
`client_timestamp_raw`, ademas de `created_at`, `updated_at`, `is_deleted` y
`deleted_at`. Ver `esquema-datos.md`.

### La cabecera X-Server-Time

Toda respuesta de la API la incluye, en ISO 8601 con milisegundos. La emite
`app/nucleo/tiempo_servidor.py`.

El reloj del telefono no es confiable y la resolucion de conflictos sera Last
Write Wins por timestamp: un telefono con la hora corrida media hora hacia
adelante ganaria todos los conflictos y borraria trabajo ajeno.

El dispositivo mide su desfase contra esta cabecera, lo guarda, y al enviar
manda las dos marcas: `client_timestamp` corregido y `client_timestamp_raw` sin
tocar. La tabla `dispositivos` ya tiene `desfase_reloj_ms` para persistirlo.

### El contrato de listado

Todo listado acepta `?updated_since=`. Con ese parametro:

- el orden cambia a `(updated_at ASC, id ASC)`, que es lo que necesita un delta
  para no saltarse registros mientras se pagina;
- **se incluyen los borrados**, porque un borrado tambien es un cambio que el
  dispositivo necesita conocer;
- el cursor lleva el modo dentro, asi que no se puede mezclar con el cursor del
  listado normal.

Esta implementado y probado en `GET /api/v1/animales`.

### La tabla sync_queue

Ya existe, con `tabla`, `registro_id`, `operacion`, `estado`, `contenido`
(JSONB), `device_id`, las dos marcas de reloj, `intentos`, `ultimo_error` y
`procesado_en`.

## Lo que falta construir

1. **Dexie.js sobre IndexedDB** con el mismo esquema que Postgres, en español.
2. **Outbox**: cada escritura de la interfaz apunta a IndexedDB y encola la
   operacion. La interfaz nunca espera a la red.
3. **Cola de binarios aparte.** Las fotos viajan como multipart y tienen otra
   politica de reintentos: no caben en el mismo outbox. `animales.foto_local_id`
   ya apunta al binario guardado en el dispositivo (decision 3).
4. **Pull delta** con `updated_since` por tabla, guardando el ultimo
   `updated_at` recibido como marca de agua.
5. **Push** del outbox, con reintento exponencial y `version` para detectar
   escrituras concurrentes.
6. **Resolucion de conflictos** Last Write Wins por `client_timestamp`
   corregido. El perdedor no se descarta en silencio: genera una alerta.
7. **Service worker y manifest** para que la aplicacion abra sin red.

## Reglas que la Fase 2 no puede romper

- **El servidor nunca rechaza un dato ya capturado en campo.** El arete
  duplicado es el caso modelo: entra marcado y genera una alerta (decision 1).
  Cualquier conflicto nuevo se resuelve con la misma forma.
- **El borrado es logico.** Un `DELETE` fisico rompe el delta: el dispositivo
  que estaba desconectado nunca se entera.
- **Las alertas derivables se calculan en el cliente** (decision 6). El
  servidor guarda estado y agregaciones de toda la finca; lo demas lo deriva el
  dispositivo con los datos que ya tiene.
- **Los catalogos son escribibles sin señal.** `catalogo_vacunas` y
  `catalogo_productos_bano` llevan `device_id` y `version` por eso (decision 4).
