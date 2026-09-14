"""Potreros y movimientos de ganado entre potreros."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencias.acceso import Alcance, require_rol
from app.esquemas.comunes import Pagina
from app.esquemas.territorio import (
    MovimientoCrear,
    MovimientoSalida,
    PotreroActualizar,
    PotreroCrear,
    PotreroSalida,
)
from app.modelos.enumeraciones import RolUsuario
from app.nucleo.paginacion import limite_valido
from app.servicios import potreros as servicio

router = APIRouter(prefix="/potreros", tags=["Potreros"])

TODOS_LOS_ROLES = [RolUsuario.administrador, RolUsuario.veterinario, RolUsuario.capataz]


# Las rutas de movimientos van antes que /{potrero_id} para que «movimientos»
# no se lea como un identificador.


@router.get(
    "/movimientos",
    response_model=Pagina[MovimientoSalida],
    summary="Historial de movimientos",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_movimientos(
    alcance: Alcance,
    potrero_id: Annotated[
        uuid.UUID | None, Query(description="Entradas y salidas de ese potrero.")
    ] = None,
    grupo_id: uuid.UUID | None = None,
    animal_id: uuid.UUID | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[MovimientoSalida]:
    datos, siguiente, hay_mas = servicio.listar_movimientos(
        alcance,
        potrero_id=potrero_id,
        grupo_id=grupo_id,
        animal_id=animal_id,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[MovimientoSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)


@router.post(
    "/movimientos",
    response_model=MovimientoSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Mover un lote o un animal de potrero",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def crear_movimiento(datos: MovimientoCrear, alcance: Alcance) -> MovimientoSalida:
    """Mueve el ganado y deja los dos potreros al dia, en una sola transaccion.

    Actualiza el potrero de cada animal, el del lote, la fecha de ultimo
    ingreso del destino y, si el origen quedo vacio, lo pone en descanso.
    Guarda cuantos animales se movieron **en ese momento**, porque el lote
    cambia y el historico tiene que seguir siendo cierto.
    """
    return servicio.mover(alcance, datos)


@router.get(
    "",
    response_model=Pagina[PotreroSalida],
    summary="Listar potreros",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_potreros(
    alcance: Alcance,
    buscar: Annotated[str | None, Query(description="Nombre, parcial.")] = None,
    solo_ocupados: Annotated[
        bool | None, Query(description="true: con ganado. false: en descanso.")
    ] = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[PotreroSalida]:
    """Cada potrero viene con cuantos animales tiene, cuanto pesan y su carga
    en unidades de ganado mayor por hectarea."""
    datos, siguiente, hay_mas = servicio.listar(
        alcance,
        buscar=buscar,
        solo_ocupados=solo_ocupados,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[PotreroSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)


@router.get(
    "/{potrero_id}",
    response_model=PotreroSalida,
    summary="Ver un potrero",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def obtener_potrero(potrero_id: uuid.UUID, alcance: Alcance) -> PotreroSalida:
    return servicio.obtener(alcance, potrero_id)


@router.post(
    "",
    response_model=PotreroSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un potrero",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def crear_potrero(datos: PotreroCrear, alcance: Alcance) -> PotreroSalida:
    return servicio.crear(alcance, datos)


@router.put(
    "/{potrero_id}",
    response_model=PotreroSalida,
    summary="Editar un potrero",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def actualizar_potrero(
    potrero_id: uuid.UUID, datos: PotreroActualizar, alcance: Alcance
) -> PotreroSalida:
    return servicio.actualizar(alcance, potrero_id, datos)


@router.delete(
    "/{potrero_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un potrero",
    dependencies=[Depends(require_rol([RolUsuario.administrador]))],
)
def eliminar_potrero(potrero_id: uuid.UUID, alcance: Alcance) -> Response:
    """Solo si el potrero quedo vacio. El borrado es logico."""
    servicio.eliminar(alcance, potrero_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
