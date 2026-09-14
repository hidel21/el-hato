"""Alertas.

Ojo con lo que NO hay aqui: no hay un endpoint que calcule los vencimientos.
Ese calculo vive en el cliente (decision 6), porque tiene que funcionar sin
señal y el dispositivo ya tiene los datos. El servidor guarda el estado.
"""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencias.acceso import Alcance, require_rol
from app.esquemas.alertas import AlertaActualizar, AlertaCrear, AlertaSalida
from app.esquemas.comunes import Pagina
from app.modelos.enumeraciones import EstadoAlerta, RolUsuario, TipoAlerta
from app.nucleo.paginacion import limite_valido
from app.servicios import alertas_estado as servicio

router = APIRouter(prefix="/alertas", tags=["Alertas"])

TODOS_LOS_ROLES = [RolUsuario.administrador, RolUsuario.veterinario, RolUsuario.capataz]


@router.get(
    "",
    response_model=Pagina[AlertaSalida],
    summary="Listar alertas",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_alertas(
    alcance: Alcance,
    estado: EstadoAlerta | None = None,
    solo_abiertas: Annotated[
        bool, Query(description="Deja fuera las atendidas y las descartadas.")
    ] = False,
    tipo: TipoAlerta | None = None,
    animal_id: uuid.UUID | None = None,
    referencia_tabla: Annotated[
        str | None, Query(description="Que tabla origino la alerta derivada.")
    ] = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[AlertaSalida]:
    """Las alertas guardadas: pendientes a mano y las derivadas ya resueltas."""
    datos, siguiente, hay_mas = servicio.listar(
        alcance,
        estado=estado,
        solo_abiertas=solo_abiertas,
        tipo=tipo,
        animal_id=animal_id,
        referencia_tabla=referencia_tabla,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[AlertaSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)


@router.post(
    "",
    response_model=AlertaSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Anotar una alerta o marcar una derivada",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def crear_alerta(datos: AlertaCrear, alcance: Alcance) -> AlertaSalida:
    """Dos usos.

    Anotar un pendiente a mano, o dejar constancia de que una alerta calculada
    en el dispositivo ya se atendio: se manda con `referencia_tabla` y
    `referencia_id`, y asi el resto de dispositivos dejan de mostrarla.

    Si ya existia una alerta para esa misma referencia, se actualiza en vez de
    duplicarse.
    """
    return servicio.crear(alcance, datos)


@router.put(
    "/{alerta_id}",
    response_model=AlertaSalida,
    summary="Cambiar el estado de una alerta",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def actualizar_alerta(
    alerta_id: uuid.UUID, datos: AlertaActualizar, alcance: Alcance
) -> AlertaSalida:
    """Atender o descartar deja anotado quien fue y cuando."""
    return servicio.actualizar(alcance, alerta_id, datos)


@router.delete(
    "/{alerta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar una alerta",
    dependencies=[Depends(require_rol([RolUsuario.administrador]))],
)
def eliminar_alerta(alerta_id: uuid.UUID, alcance: Alcance) -> Response:
    servicio.eliminar(alcance, alerta_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
