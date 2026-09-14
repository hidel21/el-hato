"""Estado de las alertas.

El calculo de lo derivable NO esta aqui y no va a estarlo: vive en el cliente
(decision 6). Este servicio solo guarda que alertas hay abiertas, cuales se
atendieron y quien las atendio, que es lo unico que tiene que viajar entre
dispositivos.
"""

import uuid
from datetime import UTC, datetime

from app.dependencias.acceso import AlcanceFinca
from app.esquemas.alertas import AlertaActualizar, AlertaCrear, AlertaSalida
from app.modelos.animal import Animal
from app.modelos.enumeraciones import EstadoAlerta, TipoAlerta
from app.modelos.operacion import Alerta
from app.modelos.organizacion import Usuario
from app.modelos.territorio import Grupo, Potrero
from app.nucleo.errores import DatosInvalidos, NoEncontrado
from app.nucleo.paginacion import (
    MODO_DELTA,
    MODO_RECIENTE,
    aplicar_orden_y_cursor,
    armar_pagina,
    decodificar_cursor,
)

# Estados que significan «ya no me la muestres».
RESUELTOS = (EstadoAlerta.atendida, EstadoAlerta.descartada)


def a_salida(alcance: AlcanceFinca, alerta: Alerta) -> AlertaSalida:
    salida = AlertaSalida.model_validate(alerta)
    if alerta.animal_id:
        animal = alcance.obtener(Animal, alerta.animal_id)
        salida.animal_arete = animal.arete if animal else None
    if alerta.atendida_por_id:
        usuario = alcance.sesion.get(Usuario, alerta.atendida_por_id)
        salida.atendida_por_nombre = usuario.nombre_completo if usuario else None
    return salida


def listar(
    alcance: AlcanceFinca,
    *,
    estado: EstadoAlerta | None = None,
    tipo: TipoAlerta | None = None,
    animal_id: uuid.UUID | None = None,
    referencia_tabla: str | None = None,
    solo_abiertas: bool = False,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[AlertaSalida], str | None, bool]:
    modo = MODO_DELTA if updated_since is not None else MODO_RECIENTE
    consulta = alcance.consultar(Alerta, incluir_borrados=updated_since is not None)

    if updated_since is not None:
        consulta = consulta.where(Alerta.updated_at > updated_since)
    if estado is not None:
        consulta = consulta.where(Alerta.estado == estado)
    if solo_abiertas:
        consulta = consulta.where(Alerta.estado.notin_(RESUELTOS))
    if tipo is not None:
        consulta = consulta.where(Alerta.tipo == tipo)
    if animal_id is not None:
        consulta = consulta.where(Alerta.animal_id == animal_id)
    if referencia_tabla is not None:
        consulta = consulta.where(Alerta.referencia_tabla == referencia_tabla)

    objeto_cursor = decodificar_cursor(cursor, modo) if cursor else None
    consulta = aplicar_orden_y_cursor(consulta, Alerta, modo, objeto_cursor)
    filas = list(alcance.sesion.execute(consulta.limit(limite + 1)).unique().scalars())

    pagina, siguiente = armar_pagina(filas, limite, modo)
    return [a_salida(alcance, a) for a in pagina], siguiente, siguiente is not None


def _validar_referencias(alcance: AlcanceFinca, datos: AlertaCrear) -> None:
    comprobaciones = (
        (datos.animal_id, Animal, "Ese animal no esta en tu finca."),
        (datos.grupo_id, Grupo, "Ese lote no esta en tu finca."),
        (datos.potrero_id, Potrero, "Ese potrero no esta en tu finca."),
    )
    for identificador, modelo, mensaje in comprobaciones:
        if identificador is not None and alcance.obtener(modelo, identificador) is None:
            raise DatosInvalidos(mensaje)


def crear(alcance: AlcanceFinca, datos: AlertaCrear) -> AlertaSalida:
    """Crea la alerta, o reusa la que ya existia para esa misma referencia.

    Si dos dispositivos marcan como atendida la misma alerta derivada, no se
    duplica: gana el ultimo y queda una sola fila.
    """
    _validar_referencias(alcance, datos)

    alerta = None
    if datos.referencia_tabla and datos.referencia_id:
        alerta = (
            alcance.sesion.execute(
                alcance.consultar(Alerta).where(
                    Alerta.referencia_tabla == datos.referencia_tabla,
                    Alerta.referencia_id == datos.referencia_id,
                    Alerta.tipo == datos.tipo,
                )
            )
            .unique()
            .scalar_one_or_none()
        )

    if alerta is None:
        valores = datos.model_dump(exclude_none=True)
        valores.pop("id", None)
        alerta = Alerta(finca_id=alcance.finca_id, **valores)
        if datos.id is not None:
            alerta.id = datos.id
        alcance.sesion.add(alerta)
    else:
        alerta.estado = datos.estado
        alerta.titulo = datos.titulo
        alerta.descripcion = datos.descripcion
        alerta.version += 1

    if alerta.estado in RESUELTOS and alerta.atendida_en is None:
        alerta.atendida_por_id = alcance.usuario.id
        alerta.atendida_en = datetime.now(UTC)

    alcance.sesion.flush()
    alcance.sesion.refresh(alerta)
    return a_salida(alcance, alerta)


def actualizar(
    alcance: AlcanceFinca, alerta_id: uuid.UUID, datos: AlertaActualizar
) -> AlertaSalida:
    alerta = alcance.obtener(Alerta, alerta_id)
    if alerta is None:
        raise NoEncontrado("Esa alerta no esta en tu finca.")

    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(alerta, campo, valor)

    if "estado" in cambios:
        if alerta.estado in RESUELTOS:
            alerta.atendida_por_id = alcance.usuario.id
            alerta.atendida_en = datetime.now(UTC)
        else:
            # Se reabre: deja de tener responsable.
            alerta.atendida_por_id = None
            alerta.atendida_en = None

    alerta.version += 1
    alcance.sesion.flush()
    alcance.sesion.refresh(alerta)
    return a_salida(alcance, alerta)


def eliminar(alcance: AlcanceFinca, alerta_id: uuid.UUID) -> None:
    alerta = alcance.obtener(Alerta, alerta_id)
    if alerta is None:
        raise NoEncontrado("Esa alerta no esta en tu finca.")

    alerta.is_deleted = True
    alerta.deleted_at = datetime.now(UTC)
    alerta.version += 1
    alcance.sesion.flush()
