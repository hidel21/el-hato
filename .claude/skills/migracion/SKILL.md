---
name: migracion
description: Escribir y verificar migraciones de Alembic en Hato — enums de Postgres, indices parciales, la vista materializada y el downgrade limpio. Usala al agregar tablas o columnas, o cuando alembic check detecte deriva.
---

# Migraciones

La migracion inicial `0001_esquema_inicial` trae el esquema completo: 21 tablas,
15 enums y la vista materializada. Toda migracion nueva se apila encima.

## El flujo

```bash
cd backend
# 1. declara el modelo en app/modelos/, con sus indices en __table_args__
.venv/bin/alembic revision --autogenerate -m "que hace"
# 2. revisa y corrige el archivo generado (ver abajo)
.venv/bin/alembic upgrade head
.venv/bin/alembic check          # no debe detectar nada
```

## Antes de dar por buena una migracion

Esto no es opcional. Las cuatro, en este orden, sin error:

```bash
.venv/bin/alembic upgrade head
.venv/bin/alembic upgrade head      # idempotente
.venv/bin/alembic downgrade base
.venv/bin/alembic downgrade base    # idempotente
.venv/bin/alembic upgrade head      # y vuelve a subir limpio
.venv/bin/alembic check             # sin deriva contra los modelos
```

## Las cuatro trampas

### 1. Los enums no se borran solos

Un `op.drop_table()` **no** borra el tipo enum que la tabla usaba. Si el
downgrade no lo elimina, el siguiente upgrade falla con «type already exists».

Patron de la migracion inicial: una lista `ENUMS` al principio del archivo, los
tipos se crean con `postgresql.ENUM(*valores, name=...).create(op.get_bind())`
antes de las tablas, las columnas los referencian con
`postgresql.ENUM(name=..., create_type=False)`, y el downgrade hace
`DROP TYPE IF EXISTS` en orden inverso.

**Agregar un valor a un enum existente** no se hace con create/drop:

```python
op.execute("ALTER TYPE alerta_tipo_enum ADD VALUE IF NOT EXISTS 'sequia'")
```

y no tiene downgrade real: Postgres no sabe quitar un valor de un enum. Dejalo
documentado en el downgrade con un comentario, no inventes un borrado.

### 2. Autogenerate no ve los indices parciales ni los GIN

Declaralos en el modelo con `__table_args__` **y** escribelos en la migracion:

```python
sa.Index(
    "idx_animales_arete_unico", "finca_id", "arete", unique=True,
    postgresql_where=sa.text("is_deleted = false AND arete_duplicado = false"),
)
sa.Index("idx_animales_arete_busqueda", "arete",
         postgresql_using="gin", postgresql_ops={"arete": "gin_trgm_ops"})
```

Si solo van en la migracion, `alembic check` los reporta como deriva para
siempre. Si solo van en el modelo, no se crean.

No pongas `DESC` en un indice de orden: Postgres recorre un btree hacia atras
sin ayuda, y una expresion `DESC` confunde a la comparacion de autogenerate.

### 3. La vista materializada es invisible para autogenerate

Se crea y se borra a mano con `op.execute`. Si cambias las columnas de
`animales` que la vista usa, tienes que recrearla en la misma migracion.

Necesita un indice **unico** sobre sus claves de agrupacion: sin el,
`REFRESH MATERIALIZED VIEW CONCURRENTLY` no funciona y cada refresco bloquea
las lecturas.

### 4. Las extensiones

`pgcrypto` (para `gen_random_uuid()`) y `pg_trgm` (para la busqueda por arete)
se crean en la migracion inicial y se borran en su downgrade. El rol del
contenedor es superusuario, asi que no hace falta nada mas.

## Reglas de columna

- PK siempre `sa.Uuid` con `default=uuid.uuid4` y
  `server_default=sa.text("gen_random_uuid()")`.
- Toda tabla raiz lleva `finca_id` con indice. Usa el mixin `DeFinca`.
- Toda tabla sincronizable hereda `Sincronizable`, que trae las ocho columnas
  comunes. `fincas` y `usuarios` usan `ConMarcaTemporal` a secas.
- Nunca `nullable=False` sin `server_default` en una tabla que ya tiene datos.
