"""Lotes.

Un lote es un grupo de animales que se maneja junto: los vientres, el levante
del norte, las terneras del año. Cambia todo el tiempo, y por eso las
aplicaciones sanitarias materializan la membresia en el momento (decision 8).
"""

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa

from app.dependencias.acceso import AlcanceFinca
from app.esquemas.territorio import GrupoActualizar, GrupoCrear, GrupoSalida
from app.modelos.animal import Animal
from app.modelos.enumeraciones import EtapaGrupo
from app.modelos.organizacion import Usuario
from app.modelos.territorio import Grupo, Potrero
from app.nucleo.errores import DatosInvalidos, ErrorAPI, NoEncontrado
from app.nucleo.paginacion import (
    MODO_DELTA,
    MODO_RECIENTE,
    aplicar_orden_y_cursor,
    armar_pagina,
    decodificar_cursor,
)
from app.servicios import inventario


def _conteos(alcance: AlcanceFinca, grupos: list[Grupo]) -> dict[uuid.UUID, int]:
    """Cuantos animales tiene hoy cada lote. Una consulta para toda la pagina."""
    if not grupos:
        return {}

    filas = alcance.sesion.execute(
        sa.select(Animal.grupo_id, sa.func.count())
        .where(
            Animal.finca_id == alcance.finca_id,
            Animal.is_deleted.is_(False),
            Animal.grupo_id.in_([grupo.id for grupo in grupos]),
        )
        .group_by(Animal.grupo_id)
    ).all()
    return dict(filas)


def a_salida(grupo: Grupo, cantidad: int = 0) -> GrupoSalida:
    salida = GrupoSalida.model_validate(grupo)
    salida.potrero_nombre = grupo.potrero.nombre if grupo.potrero else None
    salida.responsable_nombre = grupo.responsable.nombre_completo if grupo.responsable else None
    salida.cantidad_animales = cantidad
    return salida


def listar(
    alcance: AlcanceFinca,
    *,
    buscar: str | None = None,
    etapa: EtapaGrupo | None = None,
    potrero_id: uuid.UUID | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[GrupoSalida], str | None, bool]:
    modo = MODO_DELTA if updated_since is not None else MODO_RECIENTE
    consulta = alcance.consultar(Grupo, incluir_borrados=updated_since is not None)

    if updated_since is not None:
        consulta = consulta.where(Grupo.updated_at > updated_since)
    if buscar:
        consulta = consulta.where(Grupo.nombre.ilike(f"%{buscar.strip()}%"))
    if etapa is not None:
        consulta = consulta.where(Grupo.etapa == etapa)
    if potrero_id is not None:
        consulta = consulta.where(Grupo.potrero_id == potrero_id)

    objeto_cursor = decodificar_cursor(cursor, modo) if cursor else None
    consulta = aplicar_orden_y_cursor(consulta, Grupo, modo, objeto_cursor)
    filas = list(alcance.sesion.execute(consulta.limit(limite + 1)).unique().scalars())

    pagina, siguiente = armar_pagina(filas, limite, modo)
    cantidades = _conteos(alcance, pagina)
    return (
        [a_salida(grupo, cantidades.get(grupo.id, 0)) for grupo in pagina],
        siguiente,
        siguiente is not None,
    )


def obtener(alcance: AlcanceFinca, grupo_id: uuid.UUID) -> GrupoSalida:
    grupo = alcance.obtener(Grupo, grupo_id)
    if grupo is None:
        raise NoEncontrado("Ese lote no esta en tu finca.")
    return a_salida(grupo, _conteos(alcance, [grupo]).get(grupo.id, 0))


def _validar_referencias(alcance: AlcanceFinca, datos: GrupoCrear | GrupoActualizar) -> None:
    if datos.potrero_id is not None and alcance.obtener(Potrero, datos.potrero_id) is None:
        raise DatosInvalidos("Ese potrero no es de tu finca.")
    if datos.responsable_id is not None and alcance.obtener(Usuario, datos.responsable_id) is None:
        raise DatosInvalidos("Ese responsable no es de tu finca.")


def _nombre_libre(alcance: AlcanceFinca, nombre: str, excluir: uuid.UUID | None = None) -> None:
    """El nombre del lote es unico por finca.

    A diferencia del arete, un lote no se captura a la carrera en el potrero:
    lo crea alguien que esta organizando el hato y puede elegir otro nombre.
    Por eso aqui si se rechaza, con un mensaje que dice que hacer.
    """
    consulta = alcance.consultar(Grupo).where(sa.func.lower(Grupo.nombre) == nombre.lower())
    if excluir is not None:
        consulta = consulta.where(Grupo.id != excluir)
    existente = alcance.sesion.execute(consulta).unique().scalar_one_or_none()
    if existente is not None:
        # Se devuelve el nombre tal como esta guardado, no como lo escribieron:
        # asi la persona reconoce cual es el lote con el que choca.
        raise ErrorAPI("nombre_repetido", f"Ya tienes un lote llamado «{existente.nombre}».", 409)


def crear(alcance: AlcanceFinca, datos: GrupoCrear) -> GrupoSalida:
    _validar_referencias(alcance, datos)
    _nombre_libre(alcance, datos.nombre)

    valores = datos.model_dump(exclude_none=True)
    valores.pop("id", None)
    grupo = Grupo(finca_id=alcance.finca_id, **valores)
    if datos.id is not None:
        grupo.id = datos.id

    alcance.sesion.add(grupo)
    alcance.sesion.flush()
    alcance.sesion.refresh(grupo)
    return a_salida(grupo)


def actualizar(alcance: AlcanceFinca, grupo_id: uuid.UUID, datos: GrupoActualizar) -> GrupoSalida:
    grupo = alcance.obtener(Grupo, grupo_id)
    if grupo is None:
        raise NoEncontrado("Ese lote no esta en tu finca.")

    _validar_referencias(alcance, datos)
    cambios = datos.model_dump(exclude_unset=True)
    if "nombre" in cambios and cambios["nombre"] != grupo.nombre:
        _nombre_libre(alcance, cambios["nombre"], excluir=grupo.id)

    cambia_potrero = "potrero_id" in cambios and cambios["potrero_id"] != grupo.potrero_id
    for campo, valor in cambios.items():
        setattr(grupo, campo, valor)

    # Cambiar el potrero del lote desde aqui NO arrastra a los animales: para
    # eso esta el movimiento, que ademas deja historico. Se avisa en la API.
    grupo.version += 1
    alcance.sesion.flush()
    alcance.sesion.refresh(grupo)
    if cambia_potrero:
        inventario.agendar_refresco()
    return a_salida(grupo, _conteos(alcance, [grupo]).get(grupo.id, 0))


def eliminar(alcance: AlcanceFinca, grupo_id: uuid.UUID) -> None:
    """Borrado logico, y solo si el lote quedo vacio."""
    grupo = alcance.obtener(Grupo, grupo_id)
    if grupo is None:
        raise NoEncontrado("Ese lote no esta en tu finca.")

    cantidad = _conteos(alcance, [grupo]).get(grupo.id, 0)
    if cantidad:
        raise ErrorAPI(
            "lote_ocupado",
            f"«{grupo.nombre}» todavia tiene {cantidad} "
            f"{'animal' if cantidad == 1 else 'animales'}. "
            "Pasalos a otro lote antes de borrarlo.",
            409,
        )

    grupo.is_deleted = True
    grupo.deleted_at = datetime.now(UTC)
    grupo.version += 1
    alcance.sesion.flush()
