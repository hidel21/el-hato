# Hato

Sistema de gestion ganadera para fincas de cria y engorde. Lo usan tres
perfiles: administrador, veterinario y capataz. El capataz es el usuario
principal y trabaja en el potrero, a pleno sol, con una mano, con el telefono
sucio y sin señal la mayor parte del dia.

Estado: **dia 1 de 8 semanas**. Estan los cimientos y el modulo de Animales
completo, de la base de datos a la pantalla.

---

## Arrancar, en tres comandos

Necesitas Docker, Python 3.11 o mas nuevo, y Node 20 o mas nuevo.

```bash
docker compose up -d     # Postgres 16 en el puerto 5433 del host
make preparar            # entorno, dependencias, migracion y finca demo
make correr              # API en :8000 y frontend en :5173
```

Abre <http://localhost:5173> y entra con:

| Correo | Clave | Rol |
|---|---|---|
| `capataz@laguacamaya.com` | `demo1234` | capataz |
| `vet@laguacamaya.com` | `demo1234` | veterinario |
| `admin@laguacamaya.com` | `demo1234` | administrador |

La documentacion viva de la API esta en <http://localhost:8000/docs>.

### Verlo en el telefono

```bash
make movil
```

Imprime la direccion de este equipo en la red local; abrela desde el telefono
conectado al mismo WiFi. Solo se expone el frontend: la API sigue escuchando en
`localhost` y el proxy de Vite la alcanza desde el propio servidor.

Ojo: por `http://` en una IP de red local el navegador **no** considera la
pagina un contexto seguro, asi que ahi no ofrece instalarla. Para eso hace
falta HTTPS o `localhost`.

### Instalarla como aplicacion

Tiene manifest, iconos y atajos: en `http://localhost:5173` el navegador ofrece
instalarla, y arranca en pantalla completa, sin barra de direcciones.

Para instalarla en el telefono hace falta contexto seguro. Lo mas simple es por
cable, que hace que el telefono vea la app como si fuera suya:

```bash
adb reverse tcp:5173 tcp:5173    # con depuracion USB activada
```

**No lleva service worker todavia, y es a proposito.** Hoy la interfaz lee de
la red: cachear el shell haria que la aplicacion abra sin señal para mostrar
una lista vacia. Sin conexion dice «Sin señal», que es la verdad. El service
worker llega en la Fase 2 junto con Dexie y el outbox, que es cuando
offline-first deja de ser una promesa. Ver la decision 21 en
[docs/decisiones.md](docs/decisiones.md).

> **El puerto es el 5433, no el 5432**, porque en muchas maquinas el 5432 ya lo
> ocupa un Postgres instalado en el sistema. Se cambia con `POSTGRES_PUERTO` en
> `.env`.

---

## Comprobar que todo quedo bien

```bash
make tests            # 19 tests
make linter           # ruff y eslint
make reiniciar-base   # baja el esquema, lo sube y vuelve a sembrar
```

La migracion sube y baja limpia las veces que haga falta:

```bash
cd backend
.venv/bin/alembic upgrade head && .venv/bin/alembic upgrade head
.venv/bin/alembic downgrade base && .venv/bin/alembic downgrade base
.venv/bin/alembic check        # no debe detectar deriva con los modelos
```

Una prueba rapida de punta a punta desde la terminal:

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"correo":"capataz@laguacamaya.com","clave":"demo1234"}' | jq -r .token_acceso)

curl -s "localhost:8000/api/v1/animales?limite=3" -H "Authorization: Bearer $TOKEN" | jq '.datos[].arete'

# El capataz no puede borrar: responde 403
curl -s -o /dev/null -w '%{http_code}\n' -X DELETE \
  "localhost:8000/api/v1/animales/$(uuidgen)" -H "Authorization: Bearer $TOKEN"
```

---

## Que hay construido

**Base de datos.** 21 tablas, 15 enums nativos y la vista materializada
`inventario_hato`, en una sola migracion inicial. PK UUID en todas, borrado
logico en todas, `finca_id` en toda tabla raiz.

**API.** FastAPI bajo `/api/v1`. Autenticacion JWT con Argon2 (acceso de 30
minutos, refresco de 14 dias), control de acceso por rol, aislamiento
multi-tenant resuelto en una dependencia, paginacion por cursor y `updated_since`
en los listados desde el primer endpoint.

| Metodo | Ruta | Quien |
|---|---|---|
| `POST` | `/auth/login` | publico |
| `POST` | `/auth/refresh` | con token de refresco |
| `GET` | `/animales` | los tres roles |
| `GET` | `/animales/{id}` | los tres roles |
| `GET` | `/animales/{id}/genealogia` | los tres roles |
| `POST` | `/animales` | los tres roles |
| `PUT` | `/animales/{id}` | los tres roles |
| `DELETE` | `/animales/{id}` | solo administrador |

**Frontend.** React 18 con JavaScript, Vite, Tailwind y TanStack Query. Movil
primero: barra inferior de cinco posiciones con boton amarillo central, rail
lateral desde 900 px, listado y ficha en dos paneles desde 1100 px. Listado con
busqueda y filtros, ficha con genealogia, y alta de animales contra la API real.

## Que **no** hay construido, y no se construye por iniciativa propia

Dexie.js, IndexedDB, service worker, manifest de PWA, motor de sincronizacion,
los otros nueve modulos de dominio, el job programado de alertas, Docker para la
aplicacion, despliegue y observabilidad.

---

## Estructura

```
backend/          FastAPI, SQLAlchemy 2.x, Alembic
  app/nucleo/     configuracion, sesion, seguridad, errores, cursor
  app/modelos/    tablas, agrupadas por area de dominio
  app/servicios/  logica de dominio; los endpoints no consultan
  app/rutas/v1/   routers delgados
  scripts/seed.py finca demo
  tests/          19 tests
frontend/         React 18 en JavaScript, Vite, Tailwind
  src/disenio/    los cinco componentes base
  src/armazon/    estructura, navegacion, hoja de registro
  src/paginas/    pantallas
docs/             decisiones, esquema, diseño, contrato de sincronizacion
.claude/skills/   recetas para seguir construyendo
```

## Antes de tocar nada

- `docs/decisiones.md` — las decisiones cerradas y por que. Leelo antes de
  discutir alguna.
- `docs/esquema-datos.md` — las 21 tablas en texto plano.
- `docs/sistema-diseno.md` — tokens, componentes y voz de la interfaz.
- `docs/contrato-sincronizacion.md` — lo que implementara la Fase 2.

`sources/maqueta-ganadera.html` es la maqueta visual original. No hace falta
abrirla: esta destilada en `docs/sistema-diseno.md`.
