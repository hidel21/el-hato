# Hato — sistema de gestion ganadera

PWA offline-first para fincas de cria y engorde. Tres perfiles: administrador,
veterinario y capataz. El capataz es el usuario principal: trabaja en el potrero,
a pleno sol, con una mano y sin señal.

## Stack (cerrado, no proponer alternativas)

Backend  Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, psycopg 3,
         python-jose, passlib con Argon2, pytest
Base     PostgreSQL 16 con pgcrypto y pg_trgm
Front    React 18 con JavaScript (NO TypeScript), Vite, Tailwind, React Router,
         TanStack Query, React Hook Form + Zod
Entorno  Docker Compose solo para Postgres. La app corre en el host.

## Comandos

    docker compose up -d    # Postgres en el puerto 5433 del host
    make preparar           # entorno, dependencias, migracion y finca demo
    make correr             # API en :8000 y frontend en :5173
    make tests              # 88 tests de backend
    make tests-web          # 11 tests de frontend
    make linter             # ruff y eslint
    make reiniciar-base     # baja el esquema, lo sube y vuelve a sembrar

Detalle completo en la skill `entorno`.

## Convenciones no negociables

- Nombres de tablas, columnas, rutas, variables y comentarios en español.
- Toda PK es UUID; nunca autoincremental. `DEFAULT gen_random_uuid()` de respaldo.
- Toda tabla sincronizable lleva created_at, updated_at, is_deleted, deleted_at,
  device_id, version. El borrado siempre es logico.
- Multi-tenant por finca_id. El filtro vive en la dependencia `alcance_finca`,
  nunca en el cuerpo de cada endpoint.
- Prefijo `/api/v1`. Errores siempre `{"error": {"code": "...", "message": "..."}}`.
- Paginacion por cursor. Jamas offset.
- Todo listado acepta `?updated_since=`, aunque la sincronizacion sea Fase 2.
- RBAC con `require_rol(["administrador"])`, escrita una vez y reutilizada.

## Estado del proyecto

**Los diez modulos de dominio estan construidos de punta a punta**: animales,
potreros y lotes, control de peso, inventario, vacunacion, baños sanitarios,
reproduccion, gastos y alertas. Mas la pantalla del dia. 39 endpoints,
88 tests de backend y 11 de frontend.

Las alertas se **derivan en el cliente** (`frontend/src/alertas/derivar.js`,
decision 29). El servidor solo guarda su estado. No pongas un endpoint que
calcule vencimientos: la Fase 2 lo tiraria.

La aplicacion es instalable (manifest), pero sin service worker: decision 21.

NO construido todavia, y no se construye por iniciativa propia: Dexie/IndexedDB,
service worker, motor de sincronizacion, el job programado de alertas, Docker
para la app, despliegue, observabilidad.

## Donde mirar

- `docs/decisiones.md` — decisiones cerradas y su porque. Leelo antes de discutir una.
- `docs/esquema-datos.md` — las 21 tablas en texto. Evita abrir la migracion.
- `docs/sistema-diseno.md` — tokens, componentes, voz de la interfaz.
- `docs/contrato-sincronizacion.md` — lo que implementara la Fase 2.

`sources/maqueta-ganadera.html` es la fuente visual original. NO la abras: son
48 KB. Todo lo que necesitas esta destilado en la skill `interfaz`.
