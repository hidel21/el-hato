# Esquema de datos

21 tablas y una vista materializada. Este documento existe para no tener que
abrir `backend/alembic/versions/20260911_0001_esquema_inicial.py`, que son mas
de mil lineas.

## Reglas que aplican a todas

- **PK UUID**, generada en el cliente cuando exista, con `gen_random_uuid()`
  como respaldo. Nunca autoincremental.
- **Multi-tenant por `finca_id`** en toda tabla raiz, con indice.
- **Borrado logico siempre**: `is_deleted` y `deleted_at`. Nunca `DELETE`.
- **Columnas comunes** de una tabla sincronizable:

      created_at   timestamptz  NOT NULL  default now()
      updated_at   timestamptz  NOT NULL  default now()
      is_deleted   bool         NOT NULL  default false
      deleted_at   timestamptz
      device_id    varchar(100)            que dispositivo escribio
      version      int          NOT NULL  default 1
      client_timestamp      timestamptz    hora del dispositivo ya corregida
      client_timestamp_raw  timestamptz    hora cruda, para auditar

  `fincas` y `usuarios` llevan solo las cuatro primeras: en el cliente son de
  solo lectura (decision 4). `dispositivos` tampoco es sincronizable: el
  registro de un dispositivo lo hace el servidor.

## Tablas

### fincas

```
nombre                     varchar(150)  NOT NULL
codigo                     varchar(30)
municipio                  varchar(120)
departamento               varchar(120)
pais                       varchar(80)  NOT NULL
hectareas                  numeric
zona_horaria               varchar(60)  NOT NULL
moneda                     varchar(3)  NOT NULL
id                         uuid  NOT NULL
+ comunes                  created_at, deleted_at, is_deleted, updated_at
```

### usuarios

```
nombre_completo            varchar(150)  NOT NULL
correo                     varchar(180)  NOT NULL
clave_hash                 varchar(255)  NOT NULL
rol                        enum  NOT NULL
telefono                   varchar(30)
activo                     bool  NOT NULL
ultimo_acceso              timestamptz
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  created_at, deleted_at, is_deleted, updated_at
```

### dispositivos

```
usuario_id                 uuid
identificador              varchar(100)  NOT NULL
nombre                     varchar(120)
plataforma                 varchar(40)
desfase_reloj_ms           int  NOT NULL
ultima_sincronizacion      timestamptz
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  created_at, deleted_at, is_deleted, updated_at
```

### potreros

```
nombre                     varchar(120)  NOT NULL
hectareas                  numeric  NOT NULL
tipo_pasto                 enum
capacidad_ugm_ha           numeric
dias_descanso_recomendado  int  NOT NULL
en_descanso                bool  NOT NULL
fecha_ultimo_ingreso       date
observaciones              text
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### grupos

```
nombre                     varchar(120)  NOT NULL
etapa                      enum  NOT NULL
proposito                  enum  NOT NULL
potrero_id                 uuid
responsable_id             uuid
descripcion                text
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### animales

```
arete                      varchar(40)  NOT NULL
arete_duplicado            bool  NOT NULL
nombre                     varchar(120)
sexo                       enum  NOT NULL
raza                       varchar(80)
fecha_nacimiento           date
estado                     enum  NOT NULL
grupo_id                   uuid
potrero_id                 uuid
madre_id                   uuid
padre_id                   uuid
peso_nacimiento_kg         numeric
peso_actual_kg             numeric
fecha_ingreso              date
origen                     varchar(60)
fecha_salida               date
motivo_salida              varchar(160)
valor_compra               numeric
foto_url                   varchar(500)
foto_local_id              varchar(100)
observaciones              text
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### potrero_movimientos

```
potrero_origen_id          uuid
potrero_destino_id         uuid  NOT NULL
grupo_id                   uuid
animal_id                  uuid
fecha_movimiento           date  NOT NULL
cantidad_animales          int  NOT NULL
responsable_id             uuid
motivo                     varchar(160)
observaciones              text
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### catalogo_vacunas

```
nombre                     varchar(140)  NOT NULL
enfermedad                 varchar(140)
laboratorio                varchar(140)
via_aplicacion             varchar(60)
dosis_ml                   numeric
dias_refuerzo              int
dias_carencia              int  NOT NULL
obligatoria                bool  NOT NULL
activo                     bool  NOT NULL
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### vacunaciones

```
catalogo_vacuna_id         uuid  NOT NULL
animal_id                  uuid
grupo_id                   uuid
fecha_aplicacion           date  NOT NULL
proxima_dosis_fecha        date
dosis_ml                   numeric
lote_producto              varchar(80)
cantidad_animales          int  NOT NULL
costo_total                numeric
responsable_id             uuid
observaciones              text
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### vacunacion_animales

```
vacunacion_id              uuid  NOT NULL
animal_id                  uuid  NOT NULL
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### celos

```
animal_id                  uuid  NOT NULL
fecha_celo                 date  NOT NULL
metodo                     enum  NOT NULL
intensidad                 varchar(20)
responsable_id             uuid
observaciones              text
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### servicios_reproductivos

```
animal_id                  uuid  NOT NULL
celo_id                    uuid
tipo                       varchar(30)  NOT NULL
fecha_servicio             date  NOT NULL
toro_id                    uuid
pajilla_codigo             varchar(80)
inseminador_id             uuid
fecha_estimada_parto       date
costo                      numeric
observaciones              text
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### diagnosticos_prenez

```
animal_id                  uuid  NOT NULL
servicio_id                uuid
fecha_diagnostico          date  NOT NULL
resultado                  enum  NOT NULL
metodo                     varchar(40)
dias_gestacion             int
fecha_estimada_parto       date
responsable_id             uuid
observaciones              text
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### partos

```
madre_id                   uuid  NOT NULL
diagnostico_id             uuid
cria_id                    uuid
fecha_parto                date  NOT NULL
resultado                  enum  NOT NULL
dificultad                 enum  NOT NULL
peso_nacimiento_kg         numeric
responsable_id             uuid
observaciones              text
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### catalogo_productos_bano

```
nombre                     varchar(140)  NOT NULL
principio_activo           varchar(140)
laboratorio                varchar(140)
tipo                       varchar(60)
dosis_por_litro_ml         numeric
dias_carencia_carne        int  NOT NULL
dias_carencia_leche        int  NOT NULL
dias_reaplicacion          int
activo                     bool  NOT NULL
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### banos

```
producto_id                uuid  NOT NULL
grupo_id                   uuid
potrero_id                 uuid
fecha_bano                 date  NOT NULL
proxima_fecha              date
metodo                     varchar(40)
dosis_total_ml             numeric
litros_agua                numeric
cantidad_animales          int  NOT NULL
costo_total                numeric
responsable_id             uuid
observaciones              text
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### bano_animales

```
bano_id                    uuid  NOT NULL
animal_id                  uuid  NOT NULL
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### pesajes

```
animal_id                  uuid  NOT NULL
fecha_pesaje               date  NOT NULL
peso_kg                    numeric  NOT NULL
metodo                     varchar(40)
ganancia_diaria_kg         numeric
responsable_id             uuid
observaciones              text
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### gastos

```
categoria                  enum  NOT NULL
concepto                   varchar(200)  NOT NULL
monto                      numeric  NOT NULL
fecha_gasto                date  NOT NULL
animal_id                  uuid
grupo_id                   uuid
potrero_id                 uuid
proveedor                  varchar(140)
comprobante                varchar(120)
responsable_id             uuid
observaciones              text
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### alertas

```
tipo                       enum  NOT NULL
estado                     enum  NOT NULL
titulo                     varchar(200)  NOT NULL
descripcion                text
fecha_objetivo             date
animal_id                  uuid
grupo_id                   uuid
potrero_id                 uuid
referencia_tabla           varchar(60)
referencia_id              uuid
atendida_por_id            uuid
atendida_en                timestamptz
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at, version
```

### sync_queue

```
tabla                      varchar(60)  NOT NULL
registro_id                uuid  NOT NULL
operacion                  enum  NOT NULL
estado                     enum  NOT NULL
contenido                  jsonb
intentos                   int  NOT NULL
ultimo_error               text
procesado_en               timestamptz
id                         uuid  NOT NULL
finca_id                   uuid  NOT NULL
+ comunes                  client_timestamp, client_timestamp_raw, created_at, deleted_at, device_id, is_deleted, updated_at
```

## Vista materializada `inventario_hato`

Agrupa por finca, grupo, potrero, sexo y estado, contando solo animales con
`is_deleted = false`:

```
finca_id, grupo_id, grupo_nombre, potrero_id, potrero_nombre, sexo, estado,
cantidad, peso_total_kg, peso_promedio_kg, actualizado_en
```

Tiene un indice unico sobre las cinco claves de agrupacion, que es lo que
permite `REFRESH MATERIALIZED VIEW CONCURRENTLY`: sin el, cada refresco
bloquearia las lecturas y tumbaria la pantalla de inventario.

El refresco lo agenda `app/servicios/inventario.py` con debounce de 30
segundos. Nunca se refresca dentro de una peticion (decision 7).

## Indices que no son obvios

```
idx_animales_arete_unico          UNIQUE (finca_id, arete)
                                  WHERE is_deleted = false AND arete_duplicado = false
idx_animales_arete_busqueda       GIN (arete gin_trgm_ops)
idx_animales_listado              (finca_id, created_at, id) WHERE is_deleted = false
idx_animales_actualizados         (finca_id, updated_at, id)
idx_usuarios_correo_unico         UNIQUE (correo) WHERE is_deleted = false
idx_grupos_nombre_unico           UNIQUE (finca_id, nombre) WHERE is_deleted = false
idx_dispositivos_identificador_unico  UNIQUE (finca_id, identificador) WHERE is_deleted = false
idx_vacunacion_animales_unico     UNIQUE (vacunacion_id, animal_id) WHERE is_deleted = false
idx_bano_animales_unico           UNIQUE (bano_id, animal_id) WHERE is_deleted = false
idx_vacunaciones_proxima_dosis    (finca_id, proxima_dosis_fecha) parcial
idx_banos_proxima_fecha           (finca_id, proxima_fecha) parcial
idx_servicios_fecha_estimada_parto      (finca_id, fecha_estimada_parto) parcial
idx_diagnosticos_fecha_estimada_parto   (finca_id, fecha_estimada_parto) parcial
idx_pesajes_animal_fecha          (animal_id, fecha_pesaje) WHERE is_deleted = false
idx_alertas_estado                (finca_id, estado, fecha_objetivo) parcial
idx_sync_queue_estado             (finca_id, estado, created_at)
```

Los indices de orden se declaran ascendentes aunque el listado ordene al reves:
Postgres recorre un btree hacia atras sin ayuda.

Todos estan declarados en los modelos con `__table_args__`, no solo en la
migracion. Por eso `alembic check` detecta cualquier deriva entre el codigo y
la base.

## Enumeraciones

```
user_role_enum          administrador, veterinario, capataz
sexo_enum               hembra, macho
animal_estado_enum      activo, vendido, muerto, descartado, en_engorde
grupo_etapa_enum        ternero, destete, levante, engorde, vientre, toro, descarte
grupo_proposito_enum    cria, levante, engorde, leche, doble_proposito, manejo
celo_metodo_enum        observacion, parche, podometro, monta_registrada, otro
prenez_resultado_enum   prenada, vacia, dudoso
parto_resultado_enum    vivo, muerto, aborto, gemelar
parto_dificultad_enum   normal, asistido, cesarea, distocia
potrero_tipo_pasto_enum brachiaria, estrella, guinea, kikuyo, angleton,
                        pasto_natural, mezcla, otro
alerta_tipo_enum        vacunacion, bano, parto, celo, peso, rotacion,
                        inventario, otro
alerta_estado_enum      pendiente, vencida, atendida, descartada
gasto_categoria_enum    alimento, medicamento, veterinario, mano_obra, insumo,
                        transporte, mantenimiento, otro
sync_operation_enum     insert, update, delete
sync_status_enum        pendiente, enviando, enviado, error
```

Los tipos enum de Postgres **no se borran solos** al borrar las tablas. La
migracion los crea y los elimina explicitamente; sin eso, un `downgrade base`
deja los tipos huerfanos y el siguiente `upgrade` falla.
