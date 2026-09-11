"""Modulo de Animales.

El listado y la lectura los puede usar cualquier rol; el capataz es el usuario
principal. El borrado es solo del administrador.
"""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencias.acceso import Alcance, require_rol
from app.esquemas.animal import AnimalActualizar, AnimalCrear, AnimalSalida, RespuestaGenealogia
from app.esquemas.comunes import Pagina
from app.modelos.enumeraciones import EstadoAnimal, RolUsuario, Sexo
from app.nucleo.paginacion import limite_valido
from app.servicios import animales as servicio

router = APIRouter(prefix="/animales", tags=["Animales"])

TODOS_LOS_ROLES = [RolUsuario.administrador, RolUsuario.veterinario, RolUsuario.capataz]
QUIEN_REGISTRA = [RolUsuario.administrador, RolUsuario.veterinario, RolUsuario.capataz]


@router.get(
    "",
    response_model=Pagina[AnimalSalida],
    summary="Listar animales",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_animales(
    alcance: Alcance,
    buscar: Annotated[str | None, Query(description="Arete o nombre, parcial.")] = None,
    estado: EstadoAnimal | None = None,
    sexo: Sexo | None = None,
    grupo_id: uuid.UUID | None = None,
    potrero_id: uuid.UUID | None = None,
    solo_duplicados: Annotated[
        bool, Query(description="Solo fichas con el arete marcado como repetido.")
    ] = False,
    updated_since: Annotated[
        datetime | None,
        Query(
            description=(
                "Delta de sincronizacion: devuelve lo cambiado despues de esa marca, "
                "incluidos los borrados, ordenado por updated_at ascendente."
            )
        ),
    ] = None,
    cursor: Annotated[str | None, Query(description="Cursor opaco de la pagina siguiente.")] = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[AnimalSalida]:
    datos, siguiente, hay_mas = servicio.listar(
        alcance,
        buscar=buscar,
        estado=estado,
        sexo=sexo,
        grupo_id=grupo_id,
        potrero_id=potrero_id,
        solo_duplicados=solo_duplicados,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[AnimalSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)


@router.get(
    "/{animal_id}",
    response_model=AnimalSalida,
    summary="Ver una ficha",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def obtener_animal(animal_id: uuid.UUID, alcance: Alcance) -> AnimalSalida:
    return servicio.obtener(alcance, animal_id)


@router.get(
    "/{animal_id}/genealogia",
    response_model=RespuestaGenealogia,
    summary="Ver el arbol de ancestros",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def obtener_genealogia(animal_id: uuid.UUID, alcance: Alcance) -> RespuestaGenealogia:
    """Hasta tres generaciones hacia arriba: padres, abuelos y bisabuelos."""
    arbol, niveles = servicio.genealogia(alcance, animal_id)
    return RespuestaGenealogia(animal=arbol, niveles=niveles)


@router.post(
    "",
    response_model=AnimalSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta una ficha",
    dependencies=[Depends(require_rol(QUIEN_REGISTRA))],
)
def crear_animal(datos: AnimalCrear, alcance: Alcance) -> AnimalSalida:
    """Un arete repetido no se rechaza: entra marcado y genera una alerta."""
    return servicio.crear(alcance, datos)


@router.put(
    "/{animal_id}",
    response_model=AnimalSalida,
    summary="Editar una ficha",
    dependencies=[Depends(require_rol(QUIEN_REGISTRA))],
)
def actualizar_animal(
    animal_id: uuid.UUID, datos: AnimalActualizar, alcance: Alcance
) -> AnimalSalida:
    return servicio.actualizar(alcance, animal_id, datos)


@router.delete(
    "/{animal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Dar de baja una ficha",
    dependencies=[Depends(require_rol([RolUsuario.administrador]))],
)
def eliminar_animal(animal_id: uuid.UUID, alcance: Alcance) -> Response:
    """Solo el administrador. El borrado es logico: la ficha no se pierde."""
    servicio.eliminar(alcance, animal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
