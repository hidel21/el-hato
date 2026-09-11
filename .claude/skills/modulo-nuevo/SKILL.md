---
name: modulo-nuevo
description: Receta de punta a punta para agregar un modulo de dominio a Hato — pesajes, vacunacion, reproduccion, potreros, baños, gastos, alertas, grupos o inventario. Va del modelo a la pantalla siguiendo el patron ya probado en Animales. Usala al empezar cualquiera de los nueve modulos que faltan.
---

# Modulo nuevo, de punta a punta

El modulo de **Animales** es la referencia viva. Cuando dudes, abre el archivo
equivalente ahi y copia la forma, no la inventes.

Faltan nueve: grupos, vacunacion, inventario, reproduccion, potreros, baños
sanitarios, alertas, gastos y control de peso. Los modelos y las tablas **ya
existen**: la migracion inicial trae las 21. Lo que falta es la capa de arriba.

## Orden de trabajo

1. Esquemas Pydantic → 2. servicio → 3. rutas → 4. tests → 5. pantalla.
Un commit por paso terminado.

## 1. Esquemas — `app/esquemas/<modulo>.py`

Tres clases: `XCrear`, `XActualizar` (todo opcional, se envia con
`exclude_unset`) y `XSalida`.

- `XCrear` acepta `id: uuid.UUID | None` — el dispositivo puede haberlo
  generado sin señal.
- `XCrear` y `XActualizar` aceptan `device_id`, `client_timestamp` y
  `client_timestamp_raw`. Se guardan tal cual; la correccion es Fase 2.
- `XSalida` incluye `version`, `is_deleted`, `created_at` y `updated_at`: son
  parte del contrato de sincronizacion.
- Limpia el texto con `@field_validator` (recorta, normaliza mayusculas).

## 2. Servicio — `app/servicios/<modulo>.py`

**Ninguna funcion arma un `select()` suelto.** Todo sale de `AlcanceFinca`:

```python
def listar(alcance, *, updated_since=None, cursor=None, limite=50, **filtros):
    modo = MODO_DELTA if updated_since is not None else MODO_RECIENTE
    consulta = alcance.consultar(Modelo, incluir_borrados=updated_since is not None)
    if updated_since is not None:
        consulta = consulta.where(Modelo.updated_at > updated_since)
    # … filtros …
    objeto_cursor = decodificar_cursor(cursor, modo) if cursor else None
    consulta = aplicar_orden_y_cursor(consulta, Modelo, modo, objeto_cursor)
    filas = list(alcance.sesion.execute(consulta.limit(limite + 1)).unique().scalars())
    pagina, siguiente = armar_pagina(filas, limite, modo)
    return [a_salida(x) for x in pagina], siguiente, siguiente is not None
```

Reglas del servicio:

- Toda referencia a otra tabla (`grupo_id`, `animal_id`, `potrero_id`) se
  valida con `alcance.obtener(...)`: asi no se puede colgar un registro de algo
  de otra finca. Copia `_validar_referencias` de `servicios/animales.py`.
- Al editar: `objeto.version += 1`.
- Al borrar: `is_deleted = True`, `deleted_at = datetime.now(UTC)`,
  `version += 1`. Nunca `sesion.delete()`.
- Si el modulo cambia el conteo del hato (altas, bajas, cambios de grupo,
  potrero o estado), llama `inventario.agendar_refresco()` al final.
- Los errores salen de `app/nucleo/errores.py`: `NoEncontrado`, `SinPermiso`,
  `DatosInvalidos`. Nunca `HTTPException` cruda.

### Aplicaciones por lote (decision 8)

Una vacuna o un baño aplicado a un grupo **materializa la membresia** en la
misma transaccion, en `vacunacion_animales` o `bano_animales`. El grupo cambia
al dia siguiente; sin esto la trazabilidad sanitaria se pierde.

```python
animales = alcance.sesion.execute(
    alcance.consultar(Animal).where(Animal.grupo_id == datos.grupo_id)
).unique().scalars().all()

registro = Vacunacion(finca_id=alcance.finca_id, cantidad_animales=len(animales), ...)
alcance.sesion.add(registro)
alcance.sesion.flush()
alcance.sesion.add_all([
    VacunacionAnimal(finca_id=alcance.finca_id, vacunacion_id=registro.id, animal_id=a.id)
    for a in animales
])
alcance.sesion.flush()   # una sola transaccion: la cierra la dependencia
```

### Alertas (decision 6)

**No calcules en el servidor lo que el cliente puede derivar**: proxima dosis,
fecha estimada de parto, dias de carencia, dias de ocupacion de un potrero. El
dispositivo ya tiene los datos y funciona sin señal.

El servidor solo escribe en `alertas` cuando hay un conflicto entre
dispositivos (ver `alertar_arete_duplicado`) o cuando hace falta agregar toda
la finca. Guarda `estado`, no el calculo.

## 3. Rutas — `app/rutas/v1/<modulo>.py`

Router delgado: valida, llama al servicio, devuelve. Cero consultas.

```python
router = APIRouter(prefix="/pesajes", tags=["Pesajes"])

@router.get("", response_model=Pagina[PesajeSalida],
            dependencies=[Depends(require_rol(TODOS_LOS_ROLES))])
def listar_pesajes(alcance: Alcance, cursor: str | None = None,
                   limite: Annotated[int | None, Query(ge=1, le=200)] = None,
                   updated_since: datetime | None = None):
    datos, siguiente, hay_mas = servicio.listar(alcance, cursor=cursor,
                                                limite=limite_valido(limite),
                                                updated_since=updated_since)
    return Pagina[PesajeSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)
```

Quien puede que:

- **listar y ver**: los tres roles.
- **crear y editar**: los tres roles registran en campo, salvo que el dominio
  diga otra cosa (un diagnostico de preñez es del veterinario).
- **borrar**: `require_rol([RolUsuario.administrador])`, siempre logico.

Registra el router en `app/rutas/v1/__init__.py`.

## 4. Tests — `tests/test_<modulo>.py`

Cuatro como minimo, con los fixtures de `conftest.py` (`finca_a`, `finca_b`,
`cliente`, `sesion`, `cabeceras`):

1. el camino feliz de crear y listar;
2. **RBAC**: el rol que no debe, recibe 403;
3. **aislamiento**: un usuario de `finca_b` no ve ni toca lo de `finca_a`, y la
   respuesta es 404, no 403 — desde la otra finca ese registro no existe;
4. la regla propia del dominio (la membresia materializada, la carencia, el
   intervalo entre partos).

## 5. Pantalla — `frontend/src/paginas/`

Carga la skill `interfaz` antes de escribir JSX.

- Las consultas van en `src/api/<modulo>.js` con TanStack Query, siguiendo
  `api/animales.js`: `useInfiniteQuery` para listados, `getNextPageParam` desde
  `cursor_siguiente`.
- Resuelve **cargando, error y lista vacia**. Sin los tres no esta terminada.
- Reutiliza los cinco componentes base. No agregues un sexto sin decirlo.
- Reemplaza la pantalla `Proximamente` correspondiente en `App.jsx`, y agrega
  la opcion real a `HojaRegistro.jsx`.

## Lo que sigue sin construirse

Dexie, IndexedDB, service worker, manifest, motor de sincronizacion y el job
programado de alertas. No los metas de contrabando dentro de un modulo.
