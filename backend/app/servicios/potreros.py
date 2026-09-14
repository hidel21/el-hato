"""Potreros y movimientos entre potreros.

Un potrero es tierra con pasto. Lo que importa en campo es cuanto ganado
aguanta y cuantos dias lleva ocupado, porque el pasto necesita descansar.
"""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import sqlalchemy as sa

from app.dependencias.acceso import AlcanceFinca
from app.esquemas.territorio import (
    MovimientoCrear,
    MovimientoSalida,
    PotreroActualizar,
    PotreroCrear,
    PotreroSalida,
)
from app.modelos.animal import Animal
from app.modelos.territorio import Grupo, Potrero, PotreroMovimiento
from app.nucleo.errores import ErrorAPI, NoEncontrado
from app.nucleo.paginacion import (
    MODO_DELTA,
    MODO_RECIENTE,
    aplicar_orden_y_cursor,
    armar_pagina,
    decodificar_cursor,
)
from app.servicios import inventario

# Una unidad de ganado mayor son 450 kg de peso vivo. Es la medida con la que
# se compara la carga de un potrero contra lo que aguanta.
KILOS_POR_UGM = Decimal("450")


def _agregados(alcance: AlcanceFinca, potreros: list[Potrero]) -> dict[uuid.UUID, dict]:
    """Cuantos animales y cuanto peso hay hoy en cada potrero.

    Una consulta para toda la pagina, no una por fila. Es agregacion de finca
    completa: el dispositivo no la puede derivar solo (decision 6).
    """
    if not potreros:
        return {}

    identificadores = [potrero.id for potrero in potreros]

    conteo = alcance.sesion.execute(
        sa.select(
            Animal.potrero_id,
            sa.func.count().label("cantidad"),
            sa.func.coalesce(sa.func.sum(Animal.peso_actual_kg), 0).label("peso"),
        )
        .where(
            Animal.finca_id == alcance.finca_id,
            Animal.is_deleted.is_(False),
            Animal.potrero_id.in_(identificadores),
        )
        .group_by(Animal.potrero_id)
    ).all()

    lotes = alcance.sesion.execute(
        sa.select(Grupo.potrero_id, Grupo.nombre)
        .where(
            Grupo.finca_id == alcance.finca_id,
            Grupo.is_deleted.is_(False),
            Grupo.potrero_id.in_(identificadores),
        )
        .order_by(Grupo.nombre)
    ).all()

    resumen: dict[uuid.UUID, dict] = {
        identificador: {"cantidad": 0, "peso": Decimal("0"), "lotes": []}
        for identificador in identificadores
    }
    for potrero_id, cantidad, peso in conteo:
        resumen[potrero_id]["cantidad"] = cantidad
        resumen[potrero_id]["peso"] = Decimal(peso)
    for potrero_id, nombre in lotes:
        resumen[potrero_id]["lotes"].append(nombre)
    return resumen


def a_salida(potrero: Potrero, agregado: dict | None = None) -> PotreroSalida:
    salida = PotreroSalida.model_validate(potrero)
    datos = agregado or {"cantidad": 0, "peso": Decimal("0"), "lotes": []}

    salida.cantidad_animales = datos["cantidad"]
    salida.peso_total_kg = datos["peso"]
    salida.lotes = datos["lotes"]
    if potrero.hectareas and potrero.hectareas > 0:
        salida.carga_ugm_ha = round(datos["peso"] / KILOS_POR_UGM / potrero.hectareas, 2)
    return salida


def listar(
    alcance: AlcanceFinca,
    *,
    buscar: str | None = None,
    solo_ocupados: bool | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[PotreroSalida], str | None, bool]:
    modo = MODO_DELTA if updated_since is not None else MODO_RECIENTE
    consulta = alcance.consultar(Potrero, incluir_borrados=updated_since is not None)

    if updated_since is not None:
        consulta = consulta.where(Potrero.updated_at > updated_since)
    if buscar:
        consulta = consulta.where(Potrero.nombre.ilike(f"%{buscar.strip()}%"))
    if solo_ocupados is not None:
        consulta = consulta.where(Potrero.en_descanso.is_(not solo_ocupados))

    objeto_cursor = decodificar_cursor(cursor, modo) if cursor else None
    consulta = aplicar_orden_y_cursor(consulta, Potrero, modo, objeto_cursor)
    filas = list(alcance.sesion.execute(consulta.limit(limite + 1)).unique().scalars())

    pagina, siguiente = armar_pagina(filas, limite, modo)
    resumen = _agregados(alcance, pagina)
    return (
        [a_salida(potrero, resumen.get(potrero.id)) for potrero in pagina],
        siguiente,
        siguiente is not None,
    )


def obtener(alcance: AlcanceFinca, potrero_id: uuid.UUID) -> PotreroSalida:
    potrero = alcance.obtener(Potrero, potrero_id)
    if potrero is None:
        raise NoEncontrado("Ese potrero no esta en tu finca.")
    return a_salida(potrero, _agregados(alcance, [potrero]).get(potrero.id))


def _nombre_libre(alcance: AlcanceFinca, nombre: str, excluir: uuid.UUID | None = None) -> None:
    consulta = alcance.consultar(Potrero).where(sa.func.lower(Potrero.nombre) == nombre.lower())
    if excluir is not None:
        consulta = consulta.where(Potrero.id != excluir)
    existente = alcance.sesion.execute(consulta).unique().scalar_one_or_none()
    if existente is not None:
        # Se devuelve el nombre tal como esta guardado, no como lo escribieron:
        # asi la persona reconoce cual es el potrero con el que choca.
        raise ErrorAPI(
            "nombre_repetido", f"Ya tienes un potrero llamado «{existente.nombre}».", 409
        )


def crear(alcance: AlcanceFinca, datos: PotreroCrear) -> PotreroSalida:
    _nombre_libre(alcance, datos.nombre)

    valores = datos.model_dump(exclude_none=True)
    valores.pop("id", None)
    potrero = Potrero(finca_id=alcance.finca_id, **valores)
    if datos.id is not None:
        potrero.id = datos.id

    alcance.sesion.add(potrero)
    alcance.sesion.flush()
    alcance.sesion.refresh(potrero)
    return a_salida(potrero)


def actualizar(
    alcance: AlcanceFinca, potrero_id: uuid.UUID, datos: PotreroActualizar
) -> PotreroSalida:
    potrero = alcance.obtener(Potrero, potrero_id)
    if potrero is None:
        raise NoEncontrado("Ese potrero no esta en tu finca.")

    cambios = datos.model_dump(exclude_unset=True)
    if "nombre" in cambios and cambios["nombre"] != potrero.nombre:
        _nombre_libre(alcance, cambios["nombre"], excluir=potrero.id)

    for campo, valor in cambios.items():
        setattr(potrero, campo, valor)

    potrero.version += 1
    alcance.sesion.flush()
    alcance.sesion.refresh(potrero)
    return a_salida(potrero, _agregados(alcance, [potrero]).get(potrero.id))


def eliminar(alcance: AlcanceFinca, potrero_id: uuid.UUID) -> None:
    """Borrado logico, y solo si el potrero quedo vacio.

    Borrar un potrero con ganado dentro dejaria animales apuntando a tierra que
    ya no existe. Primero se mueven, despues se borra.
    """
    potrero = alcance.obtener(Potrero, potrero_id)
    if potrero is None:
        raise NoEncontrado("Ese potrero no esta en tu finca.")

    resumen = _agregados(alcance, [potrero])[potrero.id]
    if resumen["cantidad"]:
        raise ErrorAPI(
            "potrero_ocupado",
            f"«{potrero.nombre}» todavia tiene {resumen['cantidad']} "
            f"{'animal' if resumen['cantidad'] == 1 else 'animales'}. "
            "Muevelos a otro potrero antes de borrarlo.",
            409,
        )
    if resumen["lotes"]:
        raise ErrorAPI(
            "potrero_ocupado",
            f"«{potrero.nombre}» todavia tiene lotes asignados: {', '.join(resumen['lotes'])}.",
            409,
        )

    potrero.is_deleted = True
    potrero.deleted_at = datetime.now(UTC)
    potrero.version += 1
    alcance.sesion.flush()


# ----------------------------------------------------------------------
# Movimientos
# ----------------------------------------------------------------------


def a_salida_movimiento(movimiento: PotreroMovimiento) -> MovimientoSalida:
    salida = MovimientoSalida.model_validate(movimiento)
    salida.potrero_origen_nombre = (
        movimiento.potrero_origen.nombre if movimiento.potrero_origen else None
    )
    salida.potrero_destino_nombre = movimiento.potrero_destino.nombre
    salida.grupo_nombre = movimiento.grupo.nombre if movimiento.grupo else None
    salida.animal_arete = movimiento.animal.arete if movimiento.animal else None
    return salida


def mover(alcance: AlcanceFinca, datos: MovimientoCrear) -> MovimientoSalida:
    """Traslada un lote o un animal, y deja los dos potreros al dia.

    Todo ocurre en la misma transaccion: el registro del movimiento, el potrero
    de cada animal, el del lote y el estado de descanso de origen y destino. Si
    algo falla, no se mueve nada.
    """
    destino = alcance.obtener(Potrero, datos.potrero_destino_id)
    if destino is None:
        raise NoEncontrado("Ese potrero de destino no esta en tu finca.")

    fecha = datos.fecha_movimiento or date.today()
    grupo = None
    animales: list[Animal] = []
    origen_id: uuid.UUID | None = None

    if datos.grupo_id is not None:
        grupo = alcance.obtener(Grupo, datos.grupo_id)
        if grupo is None:
            raise NoEncontrado("Ese lote no esta en tu finca.")
        origen_id = grupo.potrero_id
        animales = list(
            alcance.sesion.execute(alcance.consultar(Animal).where(Animal.grupo_id == grupo.id))
            .unique()
            .scalars()
        )
    else:
        animal = alcance.obtener(Animal, datos.animal_id)
        if animal is None:
            raise NoEncontrado("Ese animal no esta en tu finca.")
        origen_id = animal.potrero_id
        animales = [animal]

    if origen_id == destino.id:
        nombre = grupo.nombre if grupo else animales[0].arete
        raise ErrorAPI("sin_movimiento", f"«{nombre}» ya esta en {destino.nombre}.", 409)

    movimiento = PotreroMovimiento(
        finca_id=alcance.finca_id,
        potrero_origen_id=origen_id,
        potrero_destino_id=destino.id,
        grupo_id=grupo.id if grupo else None,
        animal_id=None if grupo else animales[0].id,
        fecha_movimiento=fecha,
        # Se guarda cuantos se movieron en ese momento, no cuantos hay hoy:
        # el lote cambia y el historico tiene que seguir siendo cierto.
        cantidad_animales=len(animales),
        responsable_id=alcance.usuario.id,
        motivo=datos.motivo,
        observaciones=datos.observaciones,
        device_id=datos.device_id,
        client_timestamp=datos.client_timestamp,
        client_timestamp_raw=datos.client_timestamp_raw,
    )
    if datos.id is not None:
        movimiento.id = datos.id
    alcance.sesion.add(movimiento)

    for animal in animales:
        animal.potrero_id = destino.id
        animal.version += 1
    if grupo is not None:
        grupo.potrero_id = destino.id
        grupo.version += 1

    destino.fecha_ultimo_ingreso = fecha
    destino.en_descanso = False
    destino.version += 1
    alcance.sesion.flush()

    # Si el origen quedo sin ganado, empieza a descansar. Es el dato con el que
    # despues se decide cuando volver a meterle animales.
    if origen_id is not None:
        origen = alcance.obtener(Potrero, origen_id)
        if origen is not None and not _agregados(alcance, [origen])[origen.id]["cantidad"]:
            origen.en_descanso = True
            origen.version += 1

    alcance.sesion.flush()
    alcance.sesion.refresh(movimiento)
    inventario.agendar_refresco()
    return a_salida_movimiento(movimiento)


def listar_movimientos(
    alcance: AlcanceFinca,
    *,
    potrero_id: uuid.UUID | None = None,
    grupo_id: uuid.UUID | None = None,
    animal_id: uuid.UUID | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[MovimientoSalida], str | None, bool]:
    modo = MODO_DELTA if updated_since is not None else MODO_RECIENTE
    consulta = alcance.consultar(PotreroMovimiento, incluir_borrados=updated_since is not None)

    if updated_since is not None:
        consulta = consulta.where(PotreroMovimiento.updated_at > updated_since)
    if potrero_id is not None:
        consulta = consulta.where(
            sa.or_(
                PotreroMovimiento.potrero_origen_id == potrero_id,
                PotreroMovimiento.potrero_destino_id == potrero_id,
            )
        )
    if grupo_id is not None:
        consulta = consulta.where(PotreroMovimiento.grupo_id == grupo_id)
    if animal_id is not None:
        consulta = consulta.where(PotreroMovimiento.animal_id == animal_id)

    objeto_cursor = decodificar_cursor(cursor, modo) if cursor else None
    consulta = aplicar_orden_y_cursor(consulta, PotreroMovimiento, modo, objeto_cursor)
    filas = list(alcance.sesion.execute(consulta.limit(limite + 1)).unique().scalars())

    pagina, siguiente = armar_pagina(filas, limite, modo)
    return [a_salida_movimiento(m) for m in pagina], siguiente, siguiente is not None
