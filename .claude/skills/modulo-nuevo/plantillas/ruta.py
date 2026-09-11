"""Plantilla de router. Delgado: valida, llama al servicio, devuelve."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencias.acceso import Alcance, require_rol
from app.esquemas.comunes import Pagina
from app.modelos.enumeraciones import RolUsuario
from app.nucleo.paginacion import limite_valido

router = APIRouter(prefix="/RUTA", tags=["MODULO"])

TODOS_LOS_ROLES = [RolUsuario.administrador, RolUsuario.veterinario, RolUsuario.capataz]


@router.get(
    "",
    response_model=Pagina[XSalida],  # noqa: F821
    summary="Listar",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar(
    alcance: Alcance,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
):
    datos, siguiente, hay_mas = servicio.listar(  # noqa: F821
        alcance, updated_since=updated_since, cursor=cursor, limite=limite_valido(limite)
    )
    return Pagina[XSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)  # noqa: F821


@router.post(
    "",
    response_model=XSalida,  # noqa: F821
    status_code=status.HTTP_201_CREATED,
    summary="Registrar",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def crear(datos: XCrear, alcance: Alcance):  # noqa: F821
    return servicio.crear(alcance, datos)  # noqa: F821


@router.delete(
    "/{identificador}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Dar de baja",
    dependencies=[Depends(require_rol([RolUsuario.administrador]))],
)
def eliminar(identificador: uuid.UUID, alcance: Alcance) -> Response:
    servicio.eliminar(alcance, identificador)  # noqa: F821
    return Response(status_code=status.HTTP_204_NO_CONTENT)
