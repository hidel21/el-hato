"""Lotes: los grupos de animales que se manejan juntos."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencias.acceso import Alcance, require_rol
from app.esquemas.comunes import Pagina
from app.esquemas.territorio import GrupoActualizar, GrupoCrear, GrupoSalida
from app.modelos.enumeraciones import EtapaGrupo, RolUsuario
from app.nucleo.paginacion import limite_valido
from app.servicios import grupos as servicio

router = APIRouter(prefix="/grupos", tags=["Lotes"])

TODOS_LOS_ROLES = [RolUsuario.administrador, RolUsuario.veterinario, RolUsuario.capataz]


@router.get(
    "",
    response_model=Pagina[GrupoSalida],
    summary="Listar lotes",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_grupos(
    alcance: Alcance,
    buscar: Annotated[str | None, Query(description="Nombre, parcial.")] = None,
    etapa: EtapaGrupo | None = None,
    potrero_id: uuid.UUID | None = None,
    updated_since: Annotated[
        datetime | None, Query(description="Delta de sincronizacion, incluidos los borrados.")
    ] = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[GrupoSalida]:
    """Cada lote viene con cuantos animales tiene hoy."""
    datos, siguiente, hay_mas = servicio.listar(
        alcance,
        buscar=buscar,
        etapa=etapa,
        potrero_id=potrero_id,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[GrupoSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)


@router.get(
    "/{grupo_id}",
    response_model=GrupoSalida,
    summary="Ver un lote",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def obtener_grupo(grupo_id: uuid.UUID, alcance: Alcance) -> GrupoSalida:
    return servicio.obtener(alcance, grupo_id)


@router.post(
    "",
    response_model=GrupoSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un lote",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def crear_grupo(datos: GrupoCrear, alcance: Alcance) -> GrupoSalida:
    """El nombre es unico dentro de la finca: si se repite, responde 409."""
    return servicio.crear(alcance, datos)


@router.put(
    "/{grupo_id}",
    response_model=GrupoSalida,
    summary="Editar un lote",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def actualizar_grupo(grupo_id: uuid.UUID, datos: GrupoActualizar, alcance: Alcance) -> GrupoSalida:
    """Cambiar el potrero aqui NO mueve a los animales.

    Para trasladar el ganado usa `POST /potreros/movimientos`, que ademas deja
    el movimiento en el historico.
    """
    return servicio.actualizar(alcance, grupo_id, datos)


@router.delete(
    "/{grupo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un lote",
    dependencies=[Depends(require_rol([RolUsuario.administrador]))],
)
def eliminar_grupo(grupo_id: uuid.UUID, alcance: Alcance) -> Response:
    """Solo si el lote esta vacio. El borrado es logico."""
    servicio.eliminar(alcance, grupo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
