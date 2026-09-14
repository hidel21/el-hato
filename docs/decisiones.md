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

## 15. El indicador de sincronizacion no miente

La maqueta muestra «3 sin enviar». Hoy no existe el outbox, asi que no hay nada
pendiente que contar y un contador que siempre marca cero seria una mentira
pequeña que se paga cara: el capataz aprende a no creerle a la barra.

Hoy el indicador dice «Al dia» cuando hay conexion y «Sin señal» cuando no, que
es informacion verdadera y util. El contador de pendientes llega junto con el
outbox.

Por lo mismo, la banda de sin señal dice «Podras seguir registrando cuando
vuelva la conexion» y no «todo se guarda en el telefono»: eso todavia no es
cierto.

## 16. La aplicacion abre en Animales

La maqueta abre en «Hoy», pero Hoy todavia no tiene modulo. La raiz redirige a
`/animales`, que es lo unico que hoy hace algo. Cuando exista Hoy, se cambia.

## 17. Node se instalo en el directorio del usuario

La maquina no tenia Node y el paquete del sistema pide sudo. Node 22 quedo en
`~/.local/lib/node-v22.14.0-linux-x64`, con enlaces en `~/.local/bin`, que ya
esta en el PATH del usuario. Se quita con un `rm -rf` de esas rutas.

Si se prefiere el paquete del sistema: `sudo apt install nodejs npm` y borrar la
copia local.

## 18. El frontend habla con la API por el proxy de Vite

`vite.config.js` redirige `/api` a `localhost:8000`. Asi el navegador solo habla
con un origen y CORS no entra en juego en desarrollo. La API igual tiene CORS
configurado para `localhost:5173`, por si alguien prefiere apuntar directo con
`VITE_API_URL`.

## 19. React Router 7 en vez de 6

La 6 arrastra dos avisos de seguridad moderados (redireccion abierta con
contrabarra en `<Link>` y `useNavigate`, e inyeccion en la hidratacion del SSR)
que solo estan corregidos en la 7. Ninguno es explotable aqui —no hay SSR y
todos los destinos de navegacion son internos—, pero empezar ocho semanas sobre
una version con avisos abiertos no compensa.

El uso que hace la aplicacion (`BrowserRouter`, `Routes`, `Route`, `NavLink`,
`Navigate`, `useNavigate`, `useParams`) es identico en las dos. La migracion no
costo nada: `npm audit` quedo en cero y la revision en navegador pasa igual.

## 20. Sin sentencias preparadas del lado del servidor

psycopg 3 prepara las consultas en el servidor despues de unas cuantas
ejecuciones. Con la API encendida, cualquier cambio de esquema —un
`make reiniciar-base`, por ejemplo— cambia los OID de las tablas y las
conexiones del pool se quedan con planes viejos: Postgres responde
«cached plan must not change result type» y solo se arregla reiniciando.

Aparecio en la verificacion del dia 1: `GET /animales/{id}` devolvia 500
mientras el listado seguia respondiendo 200, porque cada consulta tiene su
propio plan.

El motor se crea con `connect_args={"prepare_threshold": None}`. A esta escala
la diferencia de rendimiento no se nota, y ademas es lo que exige PgBouncer en
modo transaccion, que es adonde va a ir esto en produccion.

## 21. Manifest si, service worker no

La aplicacion se puede instalar: tiene manifest, iconos, atajos y arranca en
pantalla completa sin la barra del navegador. Chrome no pone ninguna objecion
para instalarla (verificado con `Page.getInstallabilityErrors`: ninguna).

Lo que **no** lleva es service worker, y es a proposito. Hoy la interfaz lee de
la red. Un service worker que cachee el shell haria que la aplicacion abra sin
señal para mostrar una lista vacia o un error: el capataz tendria el icono de
una aplicacion que no sirve justo cuando mas la necesita, y aprenderia a no
creerle. Es la misma razon por la que el indicador no inventa un contador de
pendientes (decision 15).

Sin conexion, la aplicacion instalada se comporta igual que en el navegador:
dice «Sin señal». Eso es cierto.

El service worker llega en la Fase 2, junto con Dexie y el outbox, que es
cuando «offline-first» pasa a ser verdad y no una promesa.

**Contexto seguro.** Instalar y registrar un service worker exige HTTPS o
`localhost`. Por `http://` contra una IP de red local —que es lo que hace
`make movil`— el navegador no da contexto seguro y no ofrece instalar. Para
probar la instalacion en el telefono: `adb reverse tcp:5173 tcp:5173` por
cable, que hace que el telefono lo vea como localhost.

## 22. Los lotes viven dentro de la pantalla de potreros

La navegacion tiene cinco posiciones y ninguna es «Lotes». Antes que inventar
una sexta, la pantalla de Potreros se divide en dos pestañas: **Potreros** y
**Lotes**.

No es un apaño: en la finca el lote y el potrero son la misma conversacion
—«¿donde esta el levante?»— y quien entra a esa pantalla esta pensando en donde
esta el ganado, no en que tabla lo guarda.

## 23. El nombre repetido de un lote o un potrero SI se rechaza

Parece contradecir la decision 1, y no. Un arete se captura a la carrera en el
potrero, con una mano y sin señal: rechazarlo pierde trabajo. Un lote o un
potrero los crea alguien que esta organizando el hato, mirando la pantalla, y
que puede escribir otro nombre en dos segundos.

Asi que ahi el servidor responde 409, y el mensaje devuelve el nombre **tal como
esta guardado**, no como lo acaban de teclear: «Ya tienes un potrero llamado
"La Ceiba"». Eso es lo que permite reconocer con cual choca.

Para la Fase 2 esto es recuperable: el outbox puede reintentar con otro nombre y
avisar. No hace falta una columna de duplicado en cada tabla.

## 24. No se borra un potrero ni un lote que todavia tenga ganado

Borrar un potrero con animales dentro los dejaria apuntando a tierra que ya no
existe. El servidor responde 409 y dice cuantos son: «"La Ceiba" todavia tiene
34 animales. Muevelos a otro potrero antes de borrarlo».

Se prefirio esto a desasignarlos en silencio: un borrado no deberia cambiar
datos que nadie pidio cambiar.

## 25. Cambiar el potrero de un lote NO mueve a los animales

Editar un lote cambia la etiqueta; trasladar ganado es otra cosa y tiene su
propia operacion, `POST /potreros/movimientos`, que ademas deja historico.

Si editar el lote arrastrara a los animales, el traslado mas importante de la
finca ocurriria sin dejar rastro, y el historico de ocupacion de potreros
—que es lo que sirve para decidir la rotacion— quedaria lleno de huecos.

## 26. El movimiento congela cuantos animales se movieron

`potrero_movimientos.cantidad_animales` guarda cuantos habia **ese dia**, no
cuantos tiene el lote hoy. Es la misma razon de la decision 8: el lote cambia y
el historico tiene que seguir siendo cierto.

En la interfaz solo se mueven lotes completos. La API acepta mover un animal
suelto, y la Fase 2 lo usara; pero en el potrero se arrea el lote entero, y una
pantalla con menos decisiones es una pantalla que se usa con una mano.

## 27. La carga del potrero la calcula el servidor

Cuantos animales hay en un potrero, cuanto pesan y cual es la carga en UGM por
hectarea son agregaciones de la finca completa: un dispositivo con datos
parciales no puede responderlas bien. Las calcula el servidor, en una sola
consulta por pagina.

Los **dias de ocupacion** si los deriva el cliente desde `fecha_ultimo_ingreso`,
como manda la decision 6. Una unidad de ganado mayor son 450 kg de peso vivo.

## 28. La aplicacion abre en Hoy

La decision 16 mandaba abrir en Animales porque «Hoy» todavia no existia. Ya
existe, asi que la raiz vuelve a lo que decia la maqueta: la pantalla del dia,
que es la que responde a la pregunta con la que el capataz saca el telefono
—que hay que hacer— antes que a la de buscar un animal concreto.

## 29. Las alertas se derivan en el cliente, de verdad

La decision 6 decia que lo derivable se calcula en el cliente. Al llegar el
modulo de alertas habia que elegir si escribirlo asi o poner un endpoint que
devolviera los vencimientos ya masticados.

Se escribio en el cliente: `frontend/src/alertas/derivar.js` es una funcion
pura que recibe vacunaciones, baños, servicios, diagnosticos, partos y potreros
y devuelve las alertas agrupadas por urgencia.

Un endpoint habria sido mas facil hoy y basura mañana: la pantalla de alertas
tiene que abrir sin señal, y en la Fase 2 esos mismos datos vendran de
IndexedDB en vez de la red. La funcion no cambia; cambia de donde le llegan los
datos. Por eso es pura y por eso tiene sus propias pruebas.

Lo que si guarda el servidor es el **estado**: cuando alguien marca una alerta
como atendida se crea una fila que apunta al registro que la origino, y el
resto de dispositivos dejan de mostrarla.

## 30. Una gestacion se cierra cuando la vaca pare

Un diagnostico de preñez viejo seguia pidiendo un parto que ya habia ocurrido.
La derivacion ahora descarta la gestacion si la misma madre tiene un parto
posterior al diagnostico.

Aparecio manejando la aplicacion: la finca demo mostraba «C-0188 debio parir
hace 359 dias» cuando esa vaca ya habia parido. Es la alerta mas irritante que
puede dar un sistema, porque el capataz sabe perfectamente que esa vaca ya
pario, y una alerta que miente enseña a ignorar todas las demas.

## 31. La finca demo se siembra siempre «hoy»

`HOY` en la semilla era una fecha clavada, asi que a la semana la finca demo se
veia abandonada: ningun pesaje reciente, ningun vencimiento cerca. Ahora es
`date.today()` y todos los hechos cuelgan de ahi con desfases relativos.

Ademas cada registro nace con la marca de captura del dia en que ocurrio, no
con la de la siembra. Sin eso, la pantalla «lo que registraste hoy» mostraba
medio año de historia de golpe.

## 32. Vitest para la logica pura del frontend

La derivacion de alertas es la unica logica del frontend con ramas de verdad
—vencido contra proximo, gestacion cerrada, alertas ya atendidas— y es la que
mas caro sale si se equivoca. Lleva sus pruebas en `*.prueba.js`, con la fecha
fijada para que no dependan del calendario.

No se prueban los componentes: para eso esta la revision en navegador, que es
la que encuentra los fallos que importan en esta aplicacion.

## 33. Un formulario declarativo para las nueve acciones de campo

Pesaje, vacuna, celo, servicio, baño, gasto, diagnostico y nacimiento tienen la
misma forma: elegir a quien, poner unos datos y guardar. Estan descritas en
`frontend/src/registro/definiciones.js` y las dibuja un solo componente.

Nueve formularios casi identicos serian nueve sitios donde arreglar el mismo
detalle. El dia que haya que cambiar como se elige un animal, se cambia una vez.
