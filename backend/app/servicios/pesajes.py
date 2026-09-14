"""Control de peso.

La ganancia diaria de peso (GDP) es el numero por el que se pregunta en una
finca de engorde: cuantos kilos gana el animal cada dia. Se guarda calculada
para no recorrer el historico entero en cada listado.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import sqlalchemy as sa

from app.dependencias.acceso import AlcanceFinca
from app.esquemas.produccion import PesajeActualizar, PesajeCrear, PesajeSalida
from app.modelos.animal import Animal
from app.modelos.produccion import Pesaje
from app.nucleo.errores import DatosInvalidos, NoEncontrado
from app.nucleo.paginacion import (
    MODO_DELTA,
    MODO_RECIENTE,
    aplicar_orden_y_cursor,
    armar_pagina,
    decodificar_cursor,
)
from app.servicios import inventario


def a_salida(pesaje: Pesaje) -> PesajeSalida:
    salida = PesajeSalida.model_validate(pesaje)
    if pesaje.animal:
        salida.animal_arete = pesaje.animal.arete
        salida.animal_nombre = pesaje.animal.nombre
    return salida


def _anterior(
    alcance: AlcanceFinca, animal_id: uuid.UUID, fecha: date, excluir=None
) -> Pesaje | None:
    """El pesaje inmediatamente anterior del mismo animal."""
    consulta = (
        alcance.consultar(Pesaje)
        .where(Pesaje.animal_id == animal_id, Pesaje.fecha_pesaje < fecha)
        .order_by(Pesaje.fecha_pesaje.desc())
        .limit(1)
    )
    if excluir is not None:
        consulta = consulta.where(Pesaje.id != excluir)
    return alcance.sesion.execute(consulta).unique().scalar_one_or_none()


def _calcular_ganancia(actual: Pesaje, anterior: Pesaje | None) -> None:
    """Kilos por dia desde el pesaje anterior. Sin anterior no hay ganancia."""
    if anterior is None:
        actual.ganancia_diaria_kg = None
        return

    dias = (actual.fecha_pesaje - anterior.fecha_pesaje).days
    if dias <= 0:
        actual.ganancia_diaria_kg = None
        return

    actual.ganancia_diaria_kg = round((actual.peso_kg - anterior.peso_kg) / Decimal(dias), 3)


def _sincronizar_peso_del_animal(alcance: AlcanceFinca, animal_id: uuid.UUID) -> None:
    """La ficha del animal siempre muestra el ultimo peso registrado."""
    ultimo = (
        alcance.sesion.execute(
            alcance.consultar(Pesaje)
            .where(Pesaje.animal_id == animal_id)
            .order_by(Pesaje.fecha_pesaje.desc(), Pesaje.created_at.desc())
            .limit(1)
        )
        .unique()
        .scalar_one_or_none()
    )

    animal = alcance.obtener(Animal, animal_id)
    if animal is not None:
        animal.peso_actual_kg = ultimo.peso_kg if ultimo else None
        animal.version += 1


def _completar_comparacion(alcance: AlcanceFinca, salidas: list[PesajeSalida]) -> None:
    """Agrega cuanto subio y en cuantos dias, respecto al pesaje anterior."""
    for salida in salidas:
        anterior = _anterior(alcance, salida.animal_id, salida.fecha_pesaje, excluir=salida.id)
        if anterior is None:
            continue
        salida.diferencia_kg = salida.peso_kg - anterior.peso_kg
        salida.dias_desde_anterior = (salida.fecha_pesaje - anterior.fecha_pesaje).days


def listar(
    alcance: AlcanceFinca,
    *,
    animal_id: uuid.UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[PesajeSalida], str | None, bool]:
    modo = MODO_DELTA if updated_since is not None else MODO_RECIENTE
    consulta = alcance.consultar(Pesaje, incluir_borrados=updated_since is not None)

    if updated_since is not None:
        consulta = consulta.where(Pesaje.updated_at > updated_since)
    if animal_id is not None:
        consulta = consulta.where(Pesaje.animal_id == animal_id)
    if desde is not None:
        consulta = consulta.where(Pesaje.fecha_pesaje >= desde)
    if hasta is not None:
        consulta = consulta.where(Pesaje.fecha_pesaje <= hasta)

    objeto_cursor = decodificar_cursor(cursor, modo) if cursor else None
    consulta = aplicar_orden_y_cursor(consulta, Pesaje, modo, objeto_cursor)
    filas = list(alcance.sesion.execute(consulta.limit(limite + 1)).unique().scalars())

    pagina, siguiente = armar_pagina(filas, limite, modo)
    salidas = [a_salida(pesaje) for pesaje in pagina]
    _completar_comparacion(alcance, salidas)
    return salidas, siguiente, siguiente is not None


def obtener(alcance: AlcanceFinca, pesaje_id: uuid.UUID) -> PesajeSalida:
    pesaje = alcance.obtener(Pesaje, pesaje_id)
    if pesaje is None:
        raise NoEncontrado("Ese pesaje no esta en tu finca.")
    salida = a_salida(pesaje)
    _completar_comparacion(alcance, [salida])
    return salida


def crear(alcance: AlcanceFinca, datos: PesajeCrear) -> PesajeSalida:
    animal = alcance.obtener(Animal, datos.animal_id)
    if animal is None:
        raise DatosInvalidos("Ese animal no esta en tu finca.")

    fecha = datos.fecha_pesaje or date.today()
    if fecha > date.today():
        raise DatosInvalidos("No se puede pesar un animal en el futuro.")
    if animal.fecha_nacimiento and fecha < animal.fecha_nacimiento:
        raise DatosInvalidos("Esa fecha es anterior al nacimiento del animal.")

    valores = datos.model_dump(exclude_none=True)
    valores.pop("id", None)
    valores["fecha_pesaje"] = fecha

    pesaje = Pesaje(finca_id=alcance.finca_id, responsable_id=alcance.usuario.id, **valores)
    if datos.id is not None:
        pesaje.id = datos.id

    _calcular_ganancia(pesaje, _anterior(alcance, animal.id, fecha))
    alcance.sesion.add(pesaje)
    alcance.sesion.flush()

    _recalcular_posteriores(alcance, animal.id, fecha)
    _sincronizar_peso_del_animal(alcance, animal.id)
    alcance.sesion.flush()
    alcance.sesion.refresh(pesaje)
    inventario.agendar_refresco()

    salida = a_salida(pesaje)
    _completar_comparacion(alcance, [salida])
    return salida


def _recalcular_posteriores(alcance: AlcanceFinca, animal_id: uuid.UUID, desde: date) -> None:
    """Un pesaje que entra con fecha vieja cambia la ganancia del siguiente.

    Pasa mas de lo que parece: el capataz anota en papel y captura al final del
    dia, o llega un dato de otro dispositivo que estuvo sin señal.
    """
    posteriores = list(
        alcance.sesion.execute(
            alcance.consultar(Pesaje)
            .where(Pesaje.animal_id == animal_id, Pesaje.fecha_pesaje > desde)
            .order_by(Pesaje.fecha_pesaje.asc())
        )
        .unique()
        .scalars()
    )
    for pesaje in posteriores:
        _calcular_ganancia(pesaje, _anterior(alcance, animal_id, pesaje.fecha_pesaje, pesaje.id))


def actualizar(
    alcance: AlcanceFinca, pesaje_id: uuid.UUID, datos: PesajeActualizar
) -> PesajeSalida:
    pesaje = alcance.obtener(Pesaje, pesaje_id)
    if pesaje is None:
        raise NoEncontrado("Ese pesaje no esta en tu finca.")

    cambios = datos.model_dump(exclude_unset=True)
    fecha_vieja = pesaje.fecha_pesaje
    for campo, valor in cambios.items():
        setattr(pesaje, campo, valor)

    if pesaje.fecha_pesaje > date.today():
        raise DatosInvalidos("No se puede pesar un animal en el futuro.")

    pesaje.version += 1
    _calcular_ganancia(pesaje, _anterior(alcance, pesaje.animal_id, pesaje.fecha_pesaje, pesaje.id))
    alcance.sesion.flush()

    _recalcular_posteriores(alcance, pesaje.animal_id, min(fecha_vieja, pesaje.fecha_pesaje))
    _sincronizar_peso_del_animal(alcance, pesaje.animal_id)
    alcance.sesion.flush()
    alcance.sesion.refresh(pesaje)

    salida = a_salida(pesaje)
    _completar_comparacion(alcance, [salida])
    return salida


def eliminar(alcance: AlcanceFinca, pesaje_id: uuid.UUID) -> None:
    pesaje = alcance.obtener(Pesaje, pesaje_id)
    if pesaje is None:
        raise NoEncontrado("Ese pesaje no esta en tu finca.")

    pesaje.is_deleted = True
    pesaje.deleted_at = datetime.now(UTC)
    pesaje.version += 1
    alcance.sesion.flush()

    _recalcular_posteriores(alcance, pesaje.animal_id, pesaje.fecha_pesaje)
    _sincronizar_peso_del_animal(alcance, pesaje.animal_id)
    alcance.sesion.flush()


def historial(alcance: AlcanceFinca, animal_id: uuid.UUID) -> list[PesajeSalida]:
    """Todos los pesajes de un animal, del mas viejo al mas nuevo.

    Es lo que dibuja la grafica de la ficha. Un animal no acumula tantos
    pesajes como para que valga la pena paginarlo.
    """
    if alcance.obtener(Animal, animal_id) is None:
        raise NoEncontrado("Ese animal no esta en tu finca.")

    filas = list(
        alcance.sesion.execute(
            alcance.consultar(Pesaje)
            .where(Pesaje.animal_id == animal_id)
            .order_by(Pesaje.fecha_pesaje.asc())
            .limit(500)
        )
        .unique()
        .scalars()
    )
    salidas = [a_salida(pesaje) for pesaje in filas]
    for indice, salida in enumerate(salidas):
        if indice == 0:
            continue
        previo = salidas[indice - 1]
        salida.diferencia_kg = salida.peso_kg - previo.peso_kg
        salida.dias_desde_anterior = (salida.fecha_pesaje - previo.fecha_pesaje).days
    return salidas


def promedio_ganancia(alcance: AlcanceFinca, dias: int = 120) -> Decimal | None:
    """GDP promedio del hato en los ultimos meses.

    Es una agregacion de la finca completa, asi que la calcula el servidor
    (decision 6). Se acota en el tiempo porque un promedio que arrastra
    pesajes de hace tres años no dice nada del hato de hoy.
    """
    resultado = alcance.sesion.execute(
        sa.select(sa.func.avg(Pesaje.ganancia_diaria_kg)).where(
            Pesaje.finca_id == alcance.finca_id,
            Pesaje.is_deleted.is_(False),
            Pesaje.ganancia_diaria_kg.is_not(None),
            Pesaje.fecha_pesaje >= date.today() - timedelta(days=dias),
        )
    ).scalar()
    return round(Decimal(resultado), 3) if resultado is not None else None
