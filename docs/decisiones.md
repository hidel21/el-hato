# Decisiones de arquitectura

Cada decision dice **que** se hizo y **por que**. Las ocho primeras estaban
cerradas antes de escribir la primera linea de codigo y no se reabren.

---

## 1. Arete duplicado: el servidor nunca rechaza un dato capturado en campo

Dos capataces sin señal pueden crear el mismo arete. Rechazar el segundo
significa perder trabajo real hecho en el potrero.

`animales` lleva `arete_duplicado BOOLEAN NOT NULL DEFAULT false`. En lugar de
una restriccion `UNIQUE (finca_id, arete)` se usa un indice unico parcial:

    CREATE UNIQUE INDEX idx_animales_arete_unico ON animales(finca_id, arete)
      WHERE is_deleted = false AND arete_duplicado = false;

Al detectar colision, el servidor **acepta** el registro con
`arete_duplicado = true` y genera una alerta de tipo `otro` para que una persona
lo resuelva. El indice sigue garantizando que solo haya un animal canonico por
arete: los duplicados quedan fuera del indice.

## 2. El reloj del dispositivo no es confiable

La resolucion de conflictos sera Last Write Wins por timestamp, pero un telefono
de campo puede tener la hora corrida.

Toda respuesta de la API incluye la cabecera `X-Server-Time` en ISO 8601 con
milisegundos. Las tablas sincronizables guardan `client_timestamp` (corregido con
el desfase medido) y `client_timestamp_raw` (crudo, para auditoria). Las columnas
existen desde hoy; la correccion se aplica en Fase 2.

## 3. Fotos

`foto_url` no sirve sin conexion. `animales` lleva ademas
`foto_local_id VARCHAR(100) NULL`, que apunta al binario guardado en el
dispositivo. La cola de subida de binarios ira separada del outbox porque viaja
como multipart y tiene otra politica de reintentos. Hoy solo existe la columna.

## 4. Catalogos sincronizables, organizacion no

`catalogo_vacunas` y `catalogo_productos_bano` llevan `device_id` y `version`
porque un veterinario creara entradas sin señal.

`fincas` y `usuarios` NO los llevan: en el cliente son de solo lectura. Si
llevan `created_at`, `updated_at`, `is_deleted` y `deleted_at`, porque el borrado
logico y la auditoria aplican igual.

## 5. Tabla partos

El ciclo reproductivo no puede terminar en el diagnostico de preñez: sin parto
registrado no se puede calcular el intervalo entre partos, que es el indicador
central de un hato de cria.

`partos` enlaza madre, diagnostico y cria, y guarda resultado
(vivo/muerto/aborto/gemelar), dificultad (normal/asistido/cesarea/distocia) y
peso al nacimiento.

## 6. Las alertas derivables se calculan en el cliente

Lo que sale de los propios datos —proxima dosis, fecha estimada de parto, dias de
carencia, dias de ocupacion de un potrero— se calcula en el dispositivo, que ya
tiene los datos en IndexedDB y funciona sin señal.

La tabla `alertas` guarda solo dos cosas: el **estado** de una alerta
(pendiente/vencida/atendida/descartada), que si debe viajar entre dispositivos, y
las alertas que exigen **agregacion de toda la finca** y que un telefono no puede
derivar solo. Los servicios estan escritos con esa separacion.

## 7. La vista materializada de inventario se refresca con debounce

`inventario_hato` agrupa por finca, grupo, potrero, sexo y estado. Refrescarla
dentro de la peticion que acaba de escribir un animal convierte un alta de dos
segundos en una de quince.

El refresco se agenda con un debounce de 30 segundos: varias escrituras seguidas
producen un solo refresco. Nunca se refresca en linea dentro de la peticion.

## 8. Las aplicaciones por lote materializan la membresia

Un baño o una vacuna aplicada a «Levante Norte» debe registrar **que animales**
la recibieron en ese momento, porque el grupo cambia al dia siguiente y la
trazabilidad sanitaria se perderia.

Las tablas puente `bano_animales` y `vacunacion_animales` se escriben en la misma
transaccion que el registro padre.

---

# Decisiones menores tomadas durante la construccion

## 9. Postgres escucha en el 5433 del host

El 5432 suele estar ocupado por un Postgres instalado en el sistema. El puerto es
configurable con `POSTGRES_PUERTO` en `.env`.

## 10. Valores de los enums que no venian especificados

    sexo_enum               hembra, macho
    grupo_proposito_enum    cria, levante, engorde, leche, doble_proposito, manejo
    celo_metodo_enum        observacion, parche, podometro, monta_registrada, otro
    prenez_resultado_enum   prenada, vacia, dudoso
    potrero_tipo_pasto_enum brachiaria, estrella, guinea, kikuyo, angleton,
                            pasto_natural, mezcla, otro
    alerta_tipo_enum        vacunacion, bano, parto, celo, peso, rotacion,
                            inventario, otro
    alerta_estado_enum      pendiente, vencida, atendida, descartada
    gasto_categoria_enum    alimento, medicamento, veterinario, mano_obra,
                            insumo, transporte, mantenimiento, otro
    sync_operation_enum     insert, update, delete
    sync_status_enum        pendiente, enviando, enviado, error

## 11. El cursor cambia de orden segun el uso

La paginacion es keyset, nunca offset. El cursor es un token opaco en base64 que
lleva dentro la tupla de orden y el modo.

- Listado normal: orden `(created_at DESC, id DESC)`. Lo ultimo dado de alta
  aparece primero, que es lo que el capataz espera.
- Con `?updated_since=`: el orden se invierte a `(updated_at ASC, id ASC)`, que
  es lo que necesita un delta de sincronizacion para no saltarse registros.

El modo va dentro del cursor: un cursor de un modo no se puede usar en el otro.

## 12. Las secciones sin modulo no se dejan vacias

La navegacion tiene cinco posiciones desde el primer dia, pero hoy solo existe el
modulo de Animales. Hoy, Alertas, Potreros e Inventario renderizan una pantalla
terminada que dice en lenguaje de campo que esa parte llega despues y lleva a
Animales. No hay botones muertos ni pantallas en blanco.

Por lo mismo, la hoja del boton amarillo central abre con una sola opcion real,
«Animal nuevo». Crece cuando crezcan los modulos.

## 13. La ficha del animal es de solo lectura

El alcance del dia era listado y alta. La ficha se incluye porque el layout de
dos paneles a partir de 1100 px no existe sin ella. Consume
`GET /animales/{id}` y `/animales/{id}/genealogia`, que son endpoints de hoy.
No edita: la edicion vive en `PUT`, y su pantalla llega con el resto.

## 14. La base de pruebas se crea sola

`conftest.py` crea `ganaderia_pruebas` si no existe, conectandose a la base
`postgres`. Asi un compañero que ya tenia el volumen creado no necesita
recrearlo, y el CI no necesita un script de inicializacion aparte.
