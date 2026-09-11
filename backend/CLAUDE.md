# Backend

FastAPI + SQLAlchemy 2.x + Alembic sobre PostgreSQL 16. Todo en español:
tablas, columnas, rutas, funciones, variables y comentarios.

## Reglas que no se rompen

- **Nunca filtres por finca_id a mano dentro de un endpoint.** Usa la dependencia
  `alcance_finca` de `app/dependencias/acceso.py`, que devuelve un objeto con
  `.consultar(Modelo)` ya filtrado por la finca del token y por `is_deleted`.
  Un endpoint que arme su propio `select()` es un agujero multi-tenant.
- **RBAC con `require_rol([...])`**, nunca comparando `usuario.rol` a mano.
- **Paginacion solo por cursor** (`app/nucleo/paginacion.py`). Si ves `.offset(`
  en una consulta de listado, esta mal.
- **Borrado logico siempre**: `is_deleted = true` y `deleted_at`. Nunca `DELETE`.
- **Cada escritura sincronizable** sube `version` en uno y refresca `updated_at`.
- Los errores salen de `app/nucleo/errores.py` con el formato
  `{"error": {"code", "message"}}`. No devuelvas `detail` de FastAPI crudo.

## Donde va cada cosa

    app/nucleo/         configuracion, sesion de BD, seguridad, errores, cursor
    app/modelos/        SQLAlchemy, agrupados por area de dominio
    app/esquemas/       Pydantic v2, entrada y salida
    app/dependencias/   sesion, usuario actual, RBAC, alcance por finca
    app/servicios/      logica de dominio; los endpoints no hacen consultas
    app/rutas/v1/       routers delgados

## Migraciones

Una sola migracion inicial con el esquema completo. Antes de dar por buena
cualquier migracion nueva: `alembic upgrade head` y `alembic downgrade base`
dos veces seguidas cada uno, sin error. Los enums de Postgres no se borran solos:
el `downgrade` los elimina explicitamente.
