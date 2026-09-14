"""Gastos de la finca.

Un gasto puede ir a un animal, a un lote, a un potrero o a nada de eso. Cuando
va a un animal es lo que permite saber cuanto costo criarlo, que es la mitad de
saber si se gano dinero con el.
"""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import sqlalchemy as sa

from app.dependencias.acceso import AlcanceFinca
from app.esquemas.produccion import GastoActualizar, GastoCrear, GastoSalida, ResumenGastos
from app.modelos.animal import Animal
from app.modelos.enumeraciones import CategoriaGasto
from app.modelos.produccion import Gasto
from app.modelos.territorio import Grupo, Potrero
from app.nucleo.errores import DatosInvalidos, NoEncontrado
from app.nucleo.paginacion import (
    MODO_DELTA,
    MODO_RECIENTE,
    aplicar_orden_y_cursor,
    armar_pagina,
    decodificar_cursor,
)


def a_salida(gasto: Gasto) -> GastoSalida:
    salida = GastoSalida.model_validate(gasto)
    salida.animal_arete = gasto.animal.arete if gasto.animal else None
    salida.grupo_nombre = gasto.grupo.nombre if gasto.grupo else None
    return salida


def _validar_referencias(alcance: AlcanceFinca, datos) -> None:
    comprobaciones = (
        (datos.animal_id, Animal, "Ese animal no esta en tu finca."),
        (datos.grupo_id, Grupo, "Ese lote no esta en tu finca."),
        (datos.potrero_id, Potrero, "Ese potrero no esta en tu finca."),
    )
    for identificador, modelo, mensaje in comprobaciones:
        if identificador is not None and alcance.obtener(modelo, identificador) is None:
            raise DatosInvalidos(mensaje)


def _filtros(consulta, *, categoria, animal_id, grupo_id, desde, hasta):
    if categoria is not None:
        consulta = consulta.where(Gasto.categoria == categoria)
    if animal_id is not None:
        consulta = consulta.where(Gasto.animal_id == animal_id)
    if grupo_id is not None:
        consulta = consulta.where(Gasto.grupo_id == grupo_id)
    if desde is not None:
        consulta = consulta.where(Gasto.fecha_gasto >= desde)
    if hasta is not None:
        consulta = consulta.where(Gasto.fecha_gasto <= hasta)
    return consulta


def listar(
    alcance: AlcanceFinca,
    *,
    categoria: CategoriaGasto | None = None,
    animal_id: uuid.UUID | None = None,
    grupo_id: uuid.UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[GastoSalida], str | None, bool]:
    modo = MODO_DELTA if updated_since is not None else MODO_RECIENTE
    consulta = alcance.consultar(Gasto, incluir_borrados=updated_since is not None)
    if updated_since is not None:
        consulta = consulta.where(Gasto.updated_at > updated_since)
    consulta = _filtros(
        consulta,
        categoria=categoria,
        animal_id=animal_id,
        grupo_id=grupo_id,
        desde=desde,
        hasta=hasta,
    )

    objeto_cursor = decodificar_cursor(cursor, modo) if cursor else None
    consulta = aplicar_orden_y_cursor(consulta, Gasto, modo, objeto_cursor)
    filas = list(alcance.sesion.execute(consulta.limit(limite + 1)).unique().scalars())

    pagina, siguiente = armar_pagina(filas, limite, modo)
    return [a_salida(g) for g in pagina], siguiente, siguiente is not None


def obtener(alcance: AlcanceFinca, gasto_id: uuid.UUID) -> GastoSalida:
    gasto = alcance.obtener(Gasto, gasto_id)
    if gasto is None:
        raise NoEncontrado("Ese gasto no esta en tu finca.")
    return a_salida(gasto)


def crear(alcance: AlcanceFinca, datos: GastoCrear) -> GastoSalida:
    _validar_referencias(alcance, datos)
    fecha = datos.fecha_gasto or date.today()
    if fecha > date.today():
        raise DatosInvalidos("No se puede registrar un gasto en el futuro.")

    valores = datos.model_dump(exclude_none=True)
    valores.pop("id", None)
    valores["fecha_gasto"] = fecha

    gasto = Gasto(finca_id=alcance.finca_id, responsable_id=alcance.usuario.id, **valores)
    if datos.id is not None:
        gasto.id = datos.id

    alcance.sesion.add(gasto)
    alcance.sesion.flush()
    alcance.sesion.refresh(gasto)
    return a_salida(gasto)


def actualizar(alcance: AlcanceFinca, gasto_id: uuid.UUID, datos: GastoActualizar) -> GastoSalida:
    gasto = alcance.obtener(Gasto, gasto_id)
    if gasto is None:
        raise NoEncontrado("Ese gasto no esta en tu finca.")

    _validar_referencias(alcance, datos)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(gasto, campo, valor)

    gasto.version += 1
    alcance.sesion.flush()
    alcance.sesion.refresh(gasto)
    return a_salida(gasto)


def eliminar(alcance: AlcanceFinca, gasto_id: uuid.UUID) -> None:
    gasto = alcance.obtener(Gasto, gasto_id)
    if gasto is None:
        raise NoEncontrado("Ese gasto no esta en tu finca.")

    gasto.is_deleted = True
    gasto.deleted_at = datetime.now(UTC)
    gasto.version += 1
    alcance.sesion.flush()


def resumen(
    alcance: AlcanceFinca,
    *,
    animal_id: uuid.UUID | None = None,
    grupo_id: uuid.UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> ResumenGastos:
    """Cuanto se gasto y en que. Es agregacion de finca: la hace el servidor."""
    consulta = _filtros(
        sa.select(
            Gasto.categoria,
            sa.func.sum(Gasto.monto).label("total"),
            sa.func.count().label("cantidad"),
        ).where(Gasto.finca_id == alcance.finca_id, Gasto.is_deleted.is_(False)),
        categoria=None,
        animal_id=animal_id,
        grupo_id=grupo_id,
        desde=desde,
        hasta=hasta,
    ).group_by(Gasto.categoria)

    filas = alcance.sesion.execute(consulta).all()
    por_categoria = {categoria.value: Decimal(total) for categoria, total, _ in filas}

    return ResumenGastos(
        total=sum(por_categoria.values(), Decimal("0")),
        desde=desde,
        hasta=hasta,
        por_categoria=dict(sorted(por_categoria.items(), key=lambda par: par[1], reverse=True)),
        cantidad=sum(cantidad for _, _, cantidad in filas),
    )
