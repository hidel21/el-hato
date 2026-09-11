"""Plantilla de servicio de dominio. Copia, renombra y borra lo que sobre.

Lo unico que no se toca: todas las consultas salen de AlcanceFinca.
"""

import uuid
from datetime import UTC, datetime

from app.dependencias.acceso import AlcanceFinca
from app.nucleo.errores import DatosInvalidos, NoEncontrado
from app.nucleo.paginacion import (
    MODO_DELTA,
    MODO_RECIENTE,
    aplicar_orden_y_cursor,
    armar_pagina,
    decodificar_cursor,
)
from app.servicios import inventario


def a_salida(registro):
    """Modelo -> esquema de salida, resolviendo los nombres relacionados."""
    salida = XSalida.model_validate(registro)  # noqa: F821
    salida.animal_arete = registro.animal.arete if registro.animal else None
    return salida


def listar(alcance: AlcanceFinca, *, updated_since=None, cursor=None, limite=50):
    modo = MODO_DELTA if updated_since is not None else MODO_RECIENTE
    consulta = alcance.consultar(Modelo, incluir_borrados=updated_since is not None)  # noqa: F821

    if updated_since is not None:
        consulta = consulta.where(Modelo.updated_at > updated_since)  # noqa: F821

    objeto_cursor = decodificar_cursor(cursor, modo) if cursor else None
    consulta = aplicar_orden_y_cursor(consulta, Modelo, modo, objeto_cursor)  # noqa: F821
    filas = list(alcance.sesion.execute(consulta.limit(limite + 1)).unique().scalars())

    pagina, siguiente = armar_pagina(filas, limite, modo)
    return [a_salida(registro) for registro in pagina], siguiente, siguiente is not None


def obtener(alcance: AlcanceFinca, identificador: uuid.UUID):
    registro = alcance.obtener(Modelo, identificador)  # noqa: F821
    if registro is None:
        raise NoEncontrado("Ese registro no esta en tu finca.")
    return a_salida(registro)


def _validar_referencias(alcance: AlcanceFinca, datos) -> None:
    """Nada se cuelga de algo que no sea de la misma finca."""
    if datos.animal_id is not None and alcance.obtener(Animal, datos.animal_id) is None:  # noqa: F821
        raise DatosInvalidos("Ese animal no esta en tu finca.")


def crear(alcance: AlcanceFinca, datos):
    _validar_referencias(alcance, datos)

    valores = datos.model_dump(exclude_none=True)
    valores.pop("id", None)
    registro = Modelo(finca_id=alcance.finca_id, **valores)  # noqa: F821
    if datos.id is not None:
        registro.id = datos.id

    alcance.sesion.add(registro)
    alcance.sesion.flush()
    alcance.sesion.refresh(registro)
    inventario.agendar_refresco()  # solo si el modulo cambia el conteo del hato
    return a_salida(registro)


def actualizar(alcance: AlcanceFinca, identificador: uuid.UUID, datos):
    registro = alcance.obtener(Modelo, identificador)  # noqa: F821
    if registro is None:
        raise NoEncontrado("Ese registro no esta en tu finca.")

    _validar_referencias(alcance, datos)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(registro, campo, valor)

    registro.version += 1
    alcance.sesion.flush()
    alcance.sesion.refresh(registro)
    return a_salida(registro)


def eliminar(alcance: AlcanceFinca, identificador: uuid.UUID) -> None:
    """Borrado logico. El fisico no existe en este sistema."""
    registro = alcance.obtener(Modelo, identificador)  # noqa: F821
    if registro is None:
        raise NoEncontrado("Ese registro no esta en tu finca.")

    registro.is_deleted = True
    registro.deleted_at = datetime.now(UTC)
    registro.version += 1
    alcance.sesion.flush()
