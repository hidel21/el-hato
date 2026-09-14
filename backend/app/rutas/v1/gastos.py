"""Gastos de la finca."""

import uuid
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencias.acceso import Alcance, require_rol
from app.esquemas.comunes import Pagina
from app.esquemas.produccion import GastoActualizar, GastoCrear, GastoSalida, ResumenGastos
from app.modelos.enumeraciones import CategoriaGasto, RolUsuario
from app.nucleo.paginacion import limite_valido
from app.servicios import gastos as servicio

router = APIRouter(prefix="/gastos", tags=["Gastos"])

TODOS_LOS_ROLES = [RolUsuario.administrador, RolUsuario.veterinario, RolUsuario.capataz]


@router.get(
    "/resumen",
    response_model=ResumenGastos,
    summary="Cuanto se gasto y en que",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def resumen_gastos(
    alcance: Alcance,
    animal_id: Annotated[
        uuid.UUID | None, Query(description="Costo acumulado de ese animal.")
    ] = None,
    grupo_id: uuid.UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> ResumenGastos:
    """Con `animal_id` da el costo acumulado de criar ese animal."""
    return servicio.resumen(
        alcance, animal_id=animal_id, grupo_id=grupo_id, desde=desde, hasta=hasta
    )


@router.get(
    "",
    response_model=Pagina[GastoSalida],
    summary="Listar gastos",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_gastos(
    alcance: Alcance,
    categoria: CategoriaGasto | None = None,
    animal_id: uuid.UUID | None = None,
    grupo_id: uuid.UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[GastoSalida]:
    datos, siguiente, hay_mas = servicio.listar(
        alcance,
        categoria=categoria,
        animal_id=animal_id,
        grupo_id=grupo_id,
        desde=desde,
        hasta=hasta,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[GastoSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)


@router.get(
    "/{gasto_id}",
    response_model=GastoSalida,
    summary="Ver un gasto",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def obtener_gasto(gasto_id: uuid.UUID, alcance: Alcance) -> GastoSalida:
    return servicio.obtener(alcance, gasto_id)


@router.post(
    "",
    response_model=GastoSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un gasto",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def crear_gasto(datos: GastoCrear, alcance: Alcance) -> GastoSalida:
    """Puede ir a un animal, a un lote, a un potrero o a la finca en general."""
    return servicio.crear(alcance, datos)


@router.put(
    "/{gasto_id}",
    response_model=GastoSalida,
    summary="Corregir un gasto",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def actualizar_gasto(gasto_id: uuid.UUID, datos: GastoActualizar, alcance: Alcance) -> GastoSalida:
    return servicio.actualizar(alcance, gasto_id, datos)


@router.delete(
    "/{gasto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un gasto",
    dependencies=[Depends(require_rol([RolUsuario.administrador]))],
)
def eliminar_gasto(gasto_id: uuid.UUID, alcance: Alcance) -> Response:
    servicio.eliminar(alcance, gasto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
