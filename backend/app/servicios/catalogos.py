"""CRUD comun de los dos catalogos sanitarios.

catalogo_vacunas y catalogo_productos_bano se comportan igual: los dos son
sincronizables porque un veterinario crea entradas sin señal (decision 4), y
los dos tienen nombre unico por finca. La logica se escribe una vez.
"""

import uuid
from datetime import UTC, datetime
from typing import TypeVar

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase

from app.dependencias.acceso import AlcanceFinca
from app.nucleo.errores import ErrorAPI, NoEncontrado
from app.nucleo.paginacion import (
    MODO_DELTA,
    MODO_RECIENTE,
    aplicar_orden_y_cursor,
    armar_pagina,
    decodificar_cursor,
)

M = TypeVar("M", bound=DeclarativeBase)


def listar(
    alcance: AlcanceFinca,
    modelo: type[M],
    *,
    buscar: str | None = None,
    solo_activos: bool = False,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[M], str | None, bool]:
    modo = MODO_DELTA if updated_since is not None else MODO_RECIENTE
    consulta = alcance.consultar(modelo, incluir_borrados=updated_since is not None)

    if updated_since is not None:
        consulta = consulta.where(modelo.updated_at > updated_since)
    if buscar:
        consulta = consulta.where(modelo.nombre.ilike(f"%{buscar.strip()}%"))
    if solo_activos:
        consulta = consulta.where(modelo.activo.is_(True))

    objeto_cursor = decodificar_cursor(cursor, modo) if cursor else None
    consulta = aplicar_orden_y_cursor(consulta, modelo, modo, objeto_cursor)
    filas = list(alcance.sesion.execute(consulta.limit(limite + 1)).unique().scalars())

    pagina, siguiente = armar_pagina(filas, limite, modo)
    return pagina, siguiente, siguiente is not None


def obtener(alcance: AlcanceFinca, modelo: type[M], identificador: uuid.UUID, quees: str) -> M:
    registro = alcance.obtener(modelo, identificador)
    if registro is None:
        raise NoEncontrado(f"{quees} no esta en el catalogo de tu finca.")
    return registro


def _nombre_libre(
    alcance: AlcanceFinca, modelo: type[M], nombre: str, quees: str, excluir=None
) -> None:
    consulta = alcance.consultar(modelo).where(sa.func.lower(modelo.nombre) == nombre.lower())
    if excluir is not None:
        consulta = consulta.where(modelo.id != excluir)
    existente = alcance.sesion.execute(consulta).unique().scalar_one_or_none()
    if existente is not None:
        raise ErrorAPI(
            "nombre_repetido", f"{quees} «{existente.nombre}» ya esta en el catalogo.", 409
        )


def crear(alcance: AlcanceFinca, modelo: type[M], datos, quees: str) -> M:
    _nombre_libre(alcance, modelo, datos.nombre, quees)

    valores = datos.model_dump(exclude_none=True)
    valores.pop("id", None)
    registro = modelo(finca_id=alcance.finca_id, **valores)
    if datos.id is not None:
        registro.id = datos.id

    alcance.sesion.add(registro)
    alcance.sesion.flush()
    alcance.sesion.refresh(registro)
    return registro


def actualizar(
    alcance: AlcanceFinca, modelo: type[M], identificador: uuid.UUID, datos, quees: str
) -> M:
    registro = obtener(alcance, modelo, identificador, quees)

    cambios = datos.model_dump(exclude_unset=True)
    if "nombre" in cambios and cambios["nombre"] != registro.nombre:
        _nombre_libre(alcance, modelo, cambios["nombre"], quees, excluir=registro.id)

    for campo, valor in cambios.items():
        setattr(registro, campo, valor)

    registro.version += 1
    alcance.sesion.flush()
    alcance.sesion.refresh(registro)
    return registro


def eliminar(
    alcance: AlcanceFinca, modelo: type[M], identificador: uuid.UUID, quees: str, usos
) -> None:
    """Borrado logico. No se borra lo que ya se aplico alguna vez.

    Un producto usado en una aplicacion es parte de la trazabilidad sanitaria:
    borrarlo dejaria registros apuntando a algo que no existe. Para sacarlo de
    circulacion esta `activo = false`.
    """
    registro = obtener(alcance, modelo, identificador, quees)

    aplicado = alcance.sesion.execute(sa.select(sa.func.count()).select_from(usos)).scalar_one()
    if aplicado:
        raise ErrorAPI(
            "catalogo_en_uso",
            f"«{registro.nombre}» ya se aplico {aplicado} "
            f"{'vez' if aplicado == 1 else 'veces'}. Desactivalo en vez de borrarlo.",
            409,
        )

    registro.is_deleted = True
    registro.deleted_at = datetime.now(UTC)
    registro.version += 1
    alcance.sesion.flush()
