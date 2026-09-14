"""Ciclo reproductivo: celo, servicio, diagnostico y parto."""

import uuid
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencias.acceso import Alcance, require_rol
from app.esquemas.comunes import Pagina
from app.esquemas.reproduccion import (
    CeloCrear,
    CeloSalida,
    DiagnosticoCrear,
    DiagnosticoSalida,
    HojaReproductiva,
    PartoCrear,
    PartoSalida,
    ServicioCrear,
    ServicioSalida,
)
from app.modelos.enumeraciones import ResultadoPrenez, RolUsuario
from app.modelos.reproduccion import Celo, DiagnosticoPrenez, Parto, ServicioReproductivo
from app.nucleo.paginacion import limite_valido
from app.servicios import reproduccion as servicio

TODOS_LOS_ROLES = [RolUsuario.administrador, RolUsuario.veterinario, RolUsuario.capataz]
# Palpar y diagnosticar preñez es acto veterinario.
QUIEN_DIAGNOSTICA = [RolUsuario.administrador, RolUsuario.veterinario]
SOLO_ADMIN = [RolUsuario.administrador]

router = APIRouter(prefix="/reproduccion", tags=["Reproduccion"])


@router.get(
    "/de-animal/{animal_id}",
    response_model=HojaReproductiva,
    summary="Hoja reproductiva de una hembra",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def hoja_reproductiva(animal_id: uuid.UUID, alcance: Alcance) -> HojaReproductiva:
    """Linea de tiempo, estado actual, dias abiertos e intervalo entre partos.

    Todo sale de las fichas de ese animal, asi que la Fase 2 podra calcular lo
    mismo en el dispositivo sin señal.
    """
    return servicio.hoja_reproductiva(alcance, animal_id)


# ----------------------------------------------------------------------
# Celo
# ----------------------------------------------------------------------


@router.get(
    "/celos",
    response_model=Pagina[CeloSalida],
    summary="Listar celos",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_celos(
    alcance: Alcance,
    animal_id: uuid.UUID | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[CeloSalida]:
    datos, siguiente, hay_mas = servicio.listar_celos(
        alcance,
        animal_id=animal_id,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[CeloSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)


@router.post(
    "/celos",
    response_model=CeloSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un celo",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def registrar_celo(datos: CeloCrear, alcance: Alcance) -> CeloSalida:
    """Lo detecta quien esta en el potrero. De aqui sale el servicio."""
    return servicio.registrar_celo(alcance, datos)


@router.delete(
    "/celos/{identificador}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un celo",
    dependencies=[Depends(require_rol(SOLO_ADMIN))],
)
def eliminar_celo(identificador: uuid.UUID, alcance: Alcance) -> Response:
    servicio.eliminar(alcance, Celo, identificador, "Ese celo")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----------------------------------------------------------------------
# Servicio
# ----------------------------------------------------------------------


@router.get(
    "/servicios",
    response_model=Pagina[ServicioSalida],
    summary="Listar servicios",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_servicios(
    alcance: Alcance,
    animal_id: uuid.UUID | None = None,
    toro_id: Annotated[uuid.UUID | None, Query(description="Servicios de ese reproductor.")] = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[ServicioSalida]:
    datos, siguiente, hay_mas = servicio.listar_servicios(
        alcance,
        animal_id=animal_id,
        toro_id=toro_id,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[ServicioSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)


@router.post(
    "/servicios",
    response_model=ServicioSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un servicio",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def registrar_servicio(datos: ServicioCrear, alcance: Alcance) -> ServicioSalida:
    """Monta natural o inseminacion. Calcula la fecha estimada de parto a 283
    dias, que es lo que deja al cliente avisar sin señal."""
    return servicio.registrar_servicio(alcance, datos)


@router.delete(
    "/servicios/{identificador}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un servicio",
    dependencies=[Depends(require_rol(SOLO_ADMIN))],
)
def eliminar_servicio(identificador: uuid.UUID, alcance: Alcance) -> Response:
    servicio.eliminar(alcance, ServicioReproductivo, identificador, "Ese servicio")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----------------------------------------------------------------------
# Diagnostico
# ----------------------------------------------------------------------


@router.get(
    "/diagnosticos",
    response_model=Pagina[DiagnosticoSalida],
    summary="Listar diagnosticos de preñez",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_diagnosticos(
    alcance: Alcance,
    animal_id: uuid.UUID | None = None,
    resultado: ResultadoPrenez | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[DiagnosticoSalida]:
    datos, siguiente, hay_mas = servicio.listar_diagnosticos(
        alcance,
        animal_id=animal_id,
        resultado=resultado,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[DiagnosticoSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)


@router.post(
    "/diagnosticos",
    response_model=DiagnosticoSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un diagnostico de preñez",
    dependencies=[Depends(require_rol(QUIEN_DIAGNOSTICA))],
)
def registrar_diagnostico(datos: DiagnosticoCrear, alcance: Alcance) -> DiagnosticoSalida:
    """Palpar es acto veterinario. Si no se indica el servicio, se toma el
    ultimo anterior al diagnostico."""
    return servicio.registrar_diagnostico(alcance, datos)


@router.delete(
    "/diagnosticos/{identificador}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un diagnostico",
    dependencies=[Depends(require_rol(SOLO_ADMIN))],
)
def eliminar_diagnostico(identificador: uuid.UUID, alcance: Alcance) -> Response:
    servicio.eliminar(alcance, DiagnosticoPrenez, identificador, "Ese diagnostico")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----------------------------------------------------------------------
# Parto
# ----------------------------------------------------------------------


@router.get(
    "/partos",
    response_model=Pagina[PartoSalida],
    summary="Listar partos",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_partos(
    alcance: Alcance,
    madre_id: uuid.UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[PartoSalida]:
    """Cada parto trae el intervalo en dias desde el parto anterior de la
    misma madre, que es el indicador central de un hato de cria."""
    datos, siguiente, hay_mas = servicio.listar_partos(
        alcance,
        madre_id=madre_id,
        desde=desde,
        hasta=hasta,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[PartoSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)


@router.get(
    "/partos/{identificador}",
    response_model=PartoSalida,
    summary="Ver un parto",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def obtener_parto(identificador: uuid.UUID, alcance: Alcance) -> PartoSalida:
    return servicio.obtener_parto(alcance, identificador)


@router.post(
    "/partos",
    response_model=PartoSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un parto",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def registrar_parto(datos: PartoCrear, alcance: Alcance) -> PartoSalida:
    """Cierra la gestacion.

    Con el bloque `cria` abre de una vez la ficha del ternero, con la
    genealogia puesta: madre la que pario y padre el toro del ultimo servicio.
    Asi el nacimiento se captura una sola vez.
    """
    return servicio.registrar_parto(alcance, datos)


@router.delete(
    "/partos/{identificador}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un parto",
    dependencies=[Depends(require_rol(SOLO_ADMIN))],
)
def eliminar_parto(identificador: uuid.UUID, alcance: Alcance) -> Response:
    servicio.eliminar(alcance, Parto, identificador, "Ese parto")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
