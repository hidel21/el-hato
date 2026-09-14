"""Vacunacion y baños sanitarios, con sus catalogos."""

import uuid
from datetime import date, datetime
from typing import Annotated

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencias.acceso import Alcance, require_rol
from app.esquemas.comunes import Pagina
from app.esquemas.sanidad import (
    AnimalAplicado,
    BanoCrear,
    BanoSalida,
    ProductoBanoActualizar,
    ProductoBanoCrear,
    ProductoBanoSalida,
    VacunaActualizar,
    VacunacionCrear,
    VacunacionSalida,
    VacunaCrear,
    VacunaSalida,
)
from app.modelos.enumeraciones import RolUsuario
from app.modelos.sanidad import Bano, CatalogoProductoBano, CatalogoVacuna, Vacunacion
from app.nucleo.paginacion import limite_valido
from app.servicios import catalogos
from app.servicios import sanidad as servicio

TODOS_LOS_ROLES = [RolUsuario.administrador, RolUsuario.veterinario, RolUsuario.capataz]
# El catalogo lo mantiene quien sabe de medicamentos.
QUIEN_CURA = [RolUsuario.administrador, RolUsuario.veterinario]

router_vacunas = APIRouter(prefix="/catalogo-vacunas", tags=["Catalogo de vacunas"])
router_vacunaciones = APIRouter(prefix="/vacunaciones", tags=["Vacunacion"])
router_productos = APIRouter(prefix="/catalogo-productos-bano", tags=["Catalogo de baños"])
router_banos = APIRouter(prefix="/banos", tags=["Baños sanitarios"])


# ----------------------------------------------------------------------
# Catalogo de vacunas
# ----------------------------------------------------------------------


@router_vacunas.get(
    "",
    response_model=Pagina[VacunaSalida],
    summary="Listar el catalogo de vacunas",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_vacunas(
    alcance: Alcance,
    buscar: str | None = None,
    solo_activas: bool = False,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[VacunaSalida]:
    datos, siguiente, hay_mas = catalogos.listar(
        alcance,
        CatalogoVacuna,
        buscar=buscar,
        solo_activos=solo_activas,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[VacunaSalida](
        datos=[VacunaSalida.model_validate(v) for v in datos],
        cursor_siguiente=siguiente,
        hay_mas=hay_mas,
    )


@router_vacunas.post(
    "",
    response_model=VacunaSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar una vacuna al catalogo",
    dependencies=[Depends(require_rol(QUIEN_CURA))],
)
def crear_vacuna(datos: VacunaCrear, alcance: Alcance) -> VacunaSalida:
    """El catalogo es sincronizable: el veterinario lo alimenta sin señal."""
    return VacunaSalida.model_validate(catalogos.crear(alcance, CatalogoVacuna, datos, "La vacuna"))


@router_vacunas.put(
    "/{identificador}",
    response_model=VacunaSalida,
    summary="Editar una vacuna",
    dependencies=[Depends(require_rol(QUIEN_CURA))],
)
def actualizar_vacuna(
    identificador: uuid.UUID, datos: VacunaActualizar, alcance: Alcance
) -> VacunaSalida:
    return VacunaSalida.model_validate(
        catalogos.actualizar(alcance, CatalogoVacuna, identificador, datos, "La vacuna")
    )


@router_vacunas.delete(
    "/{identificador}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar una vacuna",
    dependencies=[Depends(require_rol([RolUsuario.administrador]))],
)
def eliminar_vacuna(identificador: uuid.UUID, alcance: Alcance) -> Response:
    """Solo si nunca se aplico. Si ya se uso, desactivala."""
    usos = (
        sa.select(Vacunacion.id)
        .where(
            Vacunacion.catalogo_vacuna_id == identificador,
            Vacunacion.finca_id == alcance.finca_id,
            Vacunacion.is_deleted.is_(False),
        )
        .subquery()
    )
    catalogos.eliminar(alcance, CatalogoVacuna, identificador, "La vacuna", usos)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----------------------------------------------------------------------
# Aplicaciones de vacuna
# ----------------------------------------------------------------------


@router_vacunaciones.get(
    "",
    response_model=Pagina[VacunacionSalida],
    summary="Listar vacunaciones",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_vacunaciones(
    alcance: Alcance,
    animal_id: Annotated[
        uuid.UUID | None, Query(description="Incluye las de lote que ese animal recibio.")
    ] = None,
    grupo_id: uuid.UUID | None = None,
    catalogo_vacuna_id: uuid.UUID | None = None,
    vence_antes_de: Annotated[
        date | None, Query(description="Refuerzos con proxima dosis hasta esa fecha.")
    ] = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[VacunacionSalida]:
    datos, siguiente, hay_mas = servicio.listar_vacunaciones(
        alcance,
        animal_id=animal_id,
        grupo_id=grupo_id,
        catalogo_vacuna_id=catalogo_vacuna_id,
        vence_antes_de=vence_antes_de,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[VacunacionSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)


@router_vacunaciones.get(
    "/{identificador}/animales",
    response_model=list[AnimalAplicado],
    summary="Que animales recibieron esa dosis",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def animales_vacunados(identificador: uuid.UUID, alcance: Alcance) -> list[AnimalAplicado]:
    """La lista congelada en el momento de aplicar (decision 8)."""
    return servicio.animales_de_vacunacion(alcance, identificador)


@router_vacunaciones.get(
    "/{identificador}",
    response_model=VacunacionSalida,
    summary="Ver una vacunacion",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def obtener_vacunacion(identificador: uuid.UUID, alcance: Alcance) -> VacunacionSalida:
    return servicio.obtener_vacunacion(alcance, identificador)


@router_vacunaciones.post(
    "",
    response_model=VacunacionSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Aplicar una vacuna",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def aplicar_vacuna(datos: VacunacionCrear, alcance: Alcance) -> VacunacionSalida:
    """A un animal o a un lote entero.

    Si es a un lote, congela quienes la recibieron en la misma transaccion.
    La proxima dosis sale de los dias de refuerzo del catalogo.
    """
    return servicio.aplicar_vacuna(alcance, datos)


@router_vacunaciones.delete(
    "/{identificador}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar una vacunacion",
    dependencies=[Depends(require_rol([RolUsuario.administrador]))],
)
def eliminar_vacunacion(identificador: uuid.UUID, alcance: Alcance) -> Response:
    servicio.eliminar_vacunacion(alcance, identificador)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----------------------------------------------------------------------
# Catalogo de productos de baño
# ----------------------------------------------------------------------


@router_productos.get(
    "",
    response_model=Pagina[ProductoBanoSalida],
    summary="Listar productos de baño",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_productos(
    alcance: Alcance,
    buscar: str | None = None,
    solo_activos: bool = False,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[ProductoBanoSalida]:
    datos, siguiente, hay_mas = catalogos.listar(
        alcance,
        CatalogoProductoBano,
        buscar=buscar,
        solo_activos=solo_activos,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[ProductoBanoSalida](
        datos=[ProductoBanoSalida.model_validate(p) for p in datos],
        cursor_siguiente=siguiente,
        hay_mas=hay_mas,
    )


@router_productos.post(
    "",
    response_model=ProductoBanoSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar un producto al catalogo",
    dependencies=[Depends(require_rol(QUIEN_CURA))],
)
def crear_producto(datos: ProductoBanoCrear, alcance: Alcance) -> ProductoBanoSalida:
    return ProductoBanoSalida.model_validate(
        catalogos.crear(alcance, CatalogoProductoBano, datos, "El producto")
    )


@router_productos.put(
    "/{identificador}",
    response_model=ProductoBanoSalida,
    summary="Editar un producto",
    dependencies=[Depends(require_rol(QUIEN_CURA))],
)
def actualizar_producto(
    identificador: uuid.UUID, datos: ProductoBanoActualizar, alcance: Alcance
) -> ProductoBanoSalida:
    return ProductoBanoSalida.model_validate(
        catalogos.actualizar(alcance, CatalogoProductoBano, identificador, datos, "El producto")
    )


@router_productos.delete(
    "/{identificador}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un producto",
    dependencies=[Depends(require_rol([RolUsuario.administrador]))],
)
def eliminar_producto(identificador: uuid.UUID, alcance: Alcance) -> Response:
    usos = (
        sa.select(Bano.id)
        .where(
            Bano.producto_id == identificador,
            Bano.finca_id == alcance.finca_id,
            Bano.is_deleted.is_(False),
        )
        .subquery()
    )
    catalogos.eliminar(alcance, CatalogoProductoBano, identificador, "El producto", usos)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----------------------------------------------------------------------
# Baños
# ----------------------------------------------------------------------


@router_banos.get(
    "",
    response_model=Pagina[BanoSalida],
    summary="Listar baños",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def listar_banos(
    alcance: Alcance,
    animal_id: uuid.UUID | None = None,
    grupo_id: uuid.UUID | None = None,
    vence_antes_de: date | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: Annotated[int | None, Query(ge=1, le=200)] = None,
) -> Pagina[BanoSalida]:
    """Cada baño dice hasta cuando corre la carencia de carne y de leche."""
    datos, siguiente, hay_mas = servicio.listar_banos(
        alcance,
        animal_id=animal_id,
        grupo_id=grupo_id,
        vence_antes_de=vence_antes_de,
        updated_since=updated_since,
        cursor=cursor,
        limite=limite_valido(limite),
    )
    return Pagina[BanoSalida](datos=datos, cursor_siguiente=siguiente, hay_mas=hay_mas)


@router_banos.get(
    "/{identificador}/animales",
    response_model=list[AnimalAplicado],
    summary="Que animales se bañaron",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def animales_banados(identificador: uuid.UUID, alcance: Alcance) -> list[AnimalAplicado]:
    return servicio.animales_de_bano(alcance, identificador)


@router_banos.get(
    "/{identificador}",
    response_model=BanoSalida,
    summary="Ver un baño",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def obtener_bano(identificador: uuid.UUID, alcance: Alcance) -> BanoSalida:
    return servicio.obtener_bano(alcance, identificador)


@router_banos.post(
    "",
    response_model=BanoSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un baño",
    dependencies=[Depends(require_rol(TODOS_LOS_ROLES))],
)
def aplicar_bano(datos: BanoCrear, alcance: Alcance) -> BanoSalida:
    """A un lote, a un potrero entero o a un animal.

    Congela quienes lo recibieron y calcula la proxima aplicacion con los dias
    de reaplicacion del producto.
    """
    return servicio.aplicar_bano(alcance, datos)


@router_banos.delete(
    "/{identificador}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un baño",
    dependencies=[Depends(require_rol([RolUsuario.administrador]))],
)
def eliminar_bano(identificador: uuid.UUID, alcance: Alcance) -> Response:
    servicio.eliminar_bano(alcance, identificador)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
