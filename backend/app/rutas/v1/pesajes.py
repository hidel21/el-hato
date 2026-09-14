"""Control de peso."""

import uuid
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencias.acceso import Alcance, require_rol
from app.esquemas.comunes import Pagina
from app.esquemas.produccion import PesajeActualizar, PesajeCrear, PesajeSalida
from app.modelos.enumeraciones import RolUsuario
from app.nucleo.paginacion import limite_valido
from app.servicios import pesajes as servicio

router = APIRouter(prefix="/pesajes", tags=["Control de peso"])

TODOS_LOS_ROLES = [RolUsuario.administrador, RolUsuario.veterinario, RolUsuario.capataz]


@router.get(
    "",
    response_model=Pagina[PesajeSalida],
    summary="Listar pesajes",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_pesajes(
    alcance: Alcance,
    animal_id: uuid.UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[PesajeSalida]:
    """Cada pesaje trae su ganancia diaria y cuanto subio desde el anterior."""
    datos, siguiente, hay_mas = servicio.listar(
        alcance,
        animal_id=animal_id,
        desde=desde,
        hasta=hasta,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[PesajeSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)


@router.get(
    "/de-animal/{animal_id}",
    response_model=list[PesajeSalida],
    summary="Historial completo de un animal",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def historial_de_animal(animal_id: uuid.UUID, alcance: Alcance) -> list[PesajeSalida]:
    """Del mas viejo al mas nuevo. Es lo que dibuja la grafica de la ficha."""
    return servicio.historial(alcance, animal_id)


@router.get(
    "/{pesaje_id}",
    response_model=PesajeSalida,
    summary="Ver un pesaje",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def obtener_pesaje(pesaje_id: uuid.UUID, alcance: Alcance) -> PesajeSalida:
    return servicio.obtener(alcance, pesaje_id)


@router.post(
    "",
    response_model=PesajeSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un pesaje",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def crear_pesaje(datos: PesajeCrear, alcance: Alcance) -> PesajeSalida:
    """Calcula la ganancia diaria contra el pesaje anterior y deja el peso
    actual del animal al dia.

    Si el pesaje entra con fecha vieja —porque se anoto en papel y se capturo
    despues—, tambien recalcula la ganancia de los pesajes posteriores.
    """
    return servicio.crear(alcance, datos)


@router.put(
    "/{pesaje_id}",
    response_model=PesajeSalida,
    summary="Corregir un pesaje",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def actualizar_pesaje(
    pesaje_id: uuid.UUID, datos: PesajeActualizar, alcance: Alcance
) -> PesajeSalida:
    return servicio.actualizar(alcance, pesaje_id, datos)


@router.delete(
    "/{pesaje_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un pesaje",
    dependencies=[Depends(require_rol([RolUsuario.administrador]))],
)
def eliminar_pesaje(pesaje_id: uuid.UUID, alcance: Alcance) -> Response:
    servicio.eliminar(alcance, pesaje_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
