---
name: entorno
description: Levantar, sembrar, resetear y correr el proyecto Hato — Postgres en Docker, migraciones de Alembic, semilla, API en el host y frontend de Vite. Usala cuando haya que arrancar el entorno, recrear la base, correr los tests o diagnosticar por que algo no conecta.
---

# Entorno de desarrollo

La app corre en el host. Docker se usa unicamente para Postgres.

## Puertos

| Servicio | Puerto | Nota |
|---|---|---|
| Postgres (contenedor) | **5433** | el 5432 del host suele estar tomado por un Postgres del sistema |
| API FastAPI | 8000 | |
| Frontend Vite | 5173 | |

## Arranque desde cero

    docker compose up -d    # Postgres, volumen ganaderia_datos_postgres
    make preparar           # .env, venv, dependencias, migracion y semilla
    make correr             # API y frontend juntos; Ctrl-C apaga los dos

A mano, si hace falta separarlo:

    cd backend
    python3 -m venv .venv
    .venv/bin/pip install -e ".[dev]"
    .venv/bin/alembic upgrade head
    .venv/bin/python scripts/seed.py
    .venv/bin/uvicorn app.main:app --reload

    cd ../frontend && npm install && npm run dev

Node vive en `~/.local/lib/node` con enlaces en `~/.local/bin`, no en el
sistema. Si `node` no aparece, revisa que `~/.local/bin` este en el PATH.

## Credenciales de la finca demo

Las crea `scripts/seed.py` sobre la finca «La Guacamaya».

| Correo | Clave | Rol |
|---|---|---|
| admin@laguacamaya.com | demo1234 | administrador |
| vet@laguacamaya.com | demo1234 | veterinario |
| capataz@laguacamaya.com | demo1234 | capataz |

## Tareas frecuentes

Resetear la base sin borrar el volumen:

    make reiniciar-base

Borrar el volumen y empezar de cero:

    docker compose down -v && docker compose up -d

Abrir psql:

    docker exec -it ganaderia_postgres psql -U ganaderia -d ganaderia

Tests (usan la base `ganaderia_pruebas`, que conftest crea sola si no existe):

    make tests

Linter y formato:

    make linter
    make formato

## Diagnostico

- `connection refused` en 5433: el contenedor no esta arriba. `docker compose ps`.
- `address already in use` al levantar: algo mas ocupa el puerto del host.
  Cambia `POSTGRES_PUERTO` en `.env` y ajusta las dos URL de conexion.
- `permission denied to create extension`: la migracion crea pgcrypto y pg_trgm,
  y necesita que el rol sea superusuario. El rol `ganaderia` del contenedor lo es.
- Enums que sobreviven a un `downgrade`: si una migracion falla a la mitad,
  revisa `\dT` en psql. Los enums se borran explicitamente en el downgrade.
