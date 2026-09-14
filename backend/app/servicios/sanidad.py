"""Vacunacion y baños sanitarios.

Decision 8: una aplicacion por lote materializa la membresia en el momento.
El lote cambia al dia siguiente; sin la lista congelada, la trazabilidad
sanitaria —que animal recibio que producto y cuando— se pierde.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import sqlalchemy as sa

from app.dependencias.acceso import AlcanceFinca
from app.esquemas.sanidad import (
    AnimalAplicado,
    BanoCrear,
    BanoSalida,
    VacunacionCrear,
    VacunacionSalida,
)
from app.modelos.animal import Animal
from app.modelos.sanidad import (
    Bano,
    BanoAnimal,
    CatalogoProductoBano,
    CatalogoVacuna,
    Vacunacion,
    VacunacionAnimal,
)
from app.modelos.territorio import Grupo, Potrero
from app.nucleo.errores import DatosInvalidos, NoEncontrado
from app.nucleo.paginacion import (
    MODO_DELTA,
    MODO_RECIENTE,
    aplicar_orden_y_cursor,
    armar_pagina,
    decodificar_cursor,
)


def _animales_alcanzados(
    alcance: AlcanceFinca,
    *,
    animal_id: uuid.UUID | None = None,
    grupo_id: uuid.UUID | None = None,
    potrero_id: uuid.UUID | None = None,
) -> list[Animal]:
    """Que animales recibe la aplicacion, resueltos ahora mismo."""
    if animal_id is not None:
        animal = alcance.obtener(Animal, animal_id)
        if animal is None:
            raise DatosInvalidos("Ese animal no esta en tu finca.")
        return [animal]

    if grupo_id is not None:
        if alcance.obtener(Grupo, grupo_id) is None:
            raise DatosInvalidos("Ese lote no esta en tu finca.")
        consulta = alcance.consultar(Animal).where(Animal.grupo_id == grupo_id)
    else:
        if alcance.obtener(Potrero, potrero_id) is None:
            raise DatosInvalidos("Ese potrero no esta en tu finca.")
        consulta = alcance.consultar(Animal).where(Animal.potrero_id == potrero_id)

    animales = list(alcance.sesion.execute(consulta).unique().scalars())
    if not animales:
        raise DatosInvalidos("Ahi no hay ningun animal al que aplicarle esto.")
    return animales


def _validar_fecha(fecha: date) -> date:
    if fecha > date.today():
        raise DatosInvalidos("No se puede registrar una aplicacion en el futuro.")
    return fecha


# ----------------------------------------------------------------------
# Vacunacion
# ----------------------------------------------------------------------


def a_salida_vacunacion(registro: Vacunacion) -> VacunacionSalida:
    salida = VacunacionSalida.model_validate(registro)
    if registro.catalogo:
        salida.vacuna_nombre = registro.catalogo.nombre
        salida.enfermedad = registro.catalogo.enfermedad
    salida.animal_arete = registro.animal.arete if registro.animal else None
    salida.grupo_nombre = registro.grupo.nombre if registro.grupo else None
    return salida


def aplicar_vacuna(alcance: AlcanceFinca, datos: VacunacionCrear) -> VacunacionSalida:
    """Registra la aplicacion y congela quienes la recibieron.

    Todo va en la misma transaccion: si algo falla, no queda ni la aplicacion
    ni la lista a medias.
    """
    vacuna = alcance.obtener(CatalogoVacuna, datos.catalogo_vacuna_id)
    if vacuna is None:
        raise DatosInvalidos("Esa vacuna no esta en el catalogo de tu finca.")

    fecha = _validar_fecha(datos.fecha_aplicacion or date.today())
    animales = _animales_alcanzados(alcance, animal_id=datos.animal_id, grupo_id=datos.grupo_id)

    # Si no dicen cuando toca el refuerzo, lo dice el catalogo.
    proxima = datos.proxima_dosis_fecha
    if proxima is None and vacuna.dias_refuerzo:
        proxima = fecha + timedelta(days=vacuna.dias_refuerzo)

    registro = Vacunacion(
        finca_id=alcance.finca_id,
        catalogo_vacuna_id=vacuna.id,
        animal_id=datos.animal_id,
        grupo_id=datos.grupo_id,
        fecha_aplicacion=fecha,
        proxima_dosis_fecha=proxima,
        dosis_ml=datos.dosis_ml or vacuna.dosis_ml,
        lote_producto=datos.lote_producto,
        cantidad_animales=len(animales),
        costo_total=datos.costo_total,
        responsable_id=alcance.usuario.id,
        observaciones=datos.observaciones,
        device_id=datos.device_id,
        client_timestamp=datos.client_timestamp,
        client_timestamp_raw=datos.client_timestamp_raw,
    )
    if datos.id is not None:
        registro.id = datos.id
    alcance.sesion.add(registro)
    alcance.sesion.flush()

    alcance.sesion.add_all(
        [
            VacunacionAnimal(
                finca_id=alcance.finca_id,
                vacunacion_id=registro.id,
                animal_id=animal.id,
                device_id=datos.device_id,
            )
            for animal in animales
        ]
    )
    alcance.sesion.flush()
    alcance.sesion.refresh(registro)
    return a_salida_vacunacion(registro)


def listar_vacunaciones(
    alcance: AlcanceFinca,
    *,
    animal_id: uuid.UUID | None = None,
    grupo_id: uuid.UUID | None = None,
    catalogo_vacuna_id: uuid.UUID | None = None,
    vence_antes_de: date | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[VacunacionSalida], str | None, bool]:
    modo = MODO_DELTA if updated_since is not None else MODO_RECIENTE
    consulta = alcance.consultar(Vacunacion, incluir_borrados=updated_since is not None)

    if updated_since is not None:
        consulta = consulta.where(Vacunacion.updated_at > updated_since)
    if animal_id is not None:
        # Incluye las de lote donde ese animal aparece en la lista congelada.
        recibidas = sa.select(VacunacionAnimal.vacunacion_id).where(
            VacunacionAnimal.animal_id == animal_id, VacunacionAnimal.is_deleted.is_(False)
        )
        consulta = consulta.where(Vacunacion.id.in_(recibidas))
    if grupo_id is not None:
        consulta = consulta.where(Vacunacion.grupo_id == grupo_id)
    if catalogo_vacuna_id is not None:
        consulta = consulta.where(Vacunacion.catalogo_vacuna_id == catalogo_vacuna_id)
    if vence_antes_de is not None:
        consulta = consulta.where(
            Vacunacion.proxima_dosis_fecha.is_not(None),
            Vacunacion.proxima_dosis_fecha <= vence_antes_de,
        )

    objeto_cursor = decodificar_cursor(cursor, modo) if cursor else None
    consulta = aplicar_orden_y_cursor(consulta, Vacunacion, modo, objeto_cursor)
    filas = list(alcance.sesion.execute(consulta.limit(limite + 1)).unique().scalars())

    pagina, siguiente = armar_pagina(filas, limite, modo)
    return [a_salida_vacunacion(v) for v in pagina], siguiente, siguiente is not None


def obtener_vacunacion(alcance: AlcanceFinca, identificador: uuid.UUID) -> VacunacionSalida:
    registro = alcance.obtener(Vacunacion, identificador)
    if registro is None:
        raise NoEncontrado("Esa vacunacion no esta en tu finca.")
    return a_salida_vacunacion(registro)


def animales_de_vacunacion(alcance: AlcanceFinca, identificador: uuid.UUID) -> list[AnimalAplicado]:
    if alcance.obtener(Vacunacion, identificador) is None:
        raise NoEncontrado("Esa vacunacion no esta en tu finca.")

    filas = list(
        alcance.sesion.execute(
            alcance.consultar(VacunacionAnimal).where(
                VacunacionAnimal.vacunacion_id == identificador
            )
        )
        .unique()
        .scalars()
    )
    return [
        AnimalAplicado(animal_id=f.animal_id, arete=f.animal.arete, nombre=f.animal.nombre)
        for f in filas
        if f.animal
    ]


def eliminar_vacunacion(alcance: AlcanceFinca, identificador: uuid.UUID) -> None:
    registro = alcance.obtener(Vacunacion, identificador)
    if registro is None:
        raise NoEncontrado("Esa vacunacion no esta en tu finca.")

    ahora = datetime.now(UTC)
    registro.is_deleted = True
    registro.deleted_at = ahora
    registro.version += 1

    # La lista congelada se va con su aplicacion: sin ella no significa nada.
    for puente in (
        alcance.sesion.execute(
            alcance.consultar(VacunacionAnimal).where(
                VacunacionAnimal.vacunacion_id == identificador
            )
        )
        .unique()
        .scalars()
    ):
        puente.is_deleted = True
        puente.deleted_at = ahora
        puente.version += 1
    alcance.sesion.flush()


# ----------------------------------------------------------------------
# Baños
# ----------------------------------------------------------------------


def a_salida_bano(registro: Bano) -> BanoSalida:
    salida = BanoSalida.model_validate(registro)
    if registro.producto:
        salida.producto_nombre = registro.producto.nombre
        if registro.producto.dias_carencia_carne:
            salida.carencia_carne_hasta = registro.fecha_bano + timedelta(
                days=registro.producto.dias_carencia_carne
            )
        if registro.producto.dias_carencia_leche:
            salida.carencia_leche_hasta = registro.fecha_bano + timedelta(
                days=registro.producto.dias_carencia_leche
            )
    salida.grupo_nombre = registro.grupo.nombre if registro.grupo else None
    salida.potrero_nombre = registro.potrero.nombre if registro.potrero else None
    return salida


def aplicar_bano(alcance: AlcanceFinca, datos: BanoCrear) -> BanoSalida:
    producto = alcance.obtener(CatalogoProductoBano, datos.producto_id)
    if producto is None:
        raise DatosInvalidos("Ese producto no esta en el catalogo de tu finca.")

    fecha = _validar_fecha(datos.fecha_bano or date.today())
    animales = _animales_alcanzados(
        alcance,
        animal_id=datos.animal_id,
        grupo_id=datos.grupo_id,
        potrero_id=datos.potrero_id,
    )

    proxima = datos.proxima_fecha
    if proxima is None and producto.dias_reaplicacion:
        proxima = fecha + timedelta(days=producto.dias_reaplicacion)

    registro = Bano(
        finca_id=alcance.finca_id,
        producto_id=producto.id,
        grupo_id=datos.grupo_id,
        potrero_id=datos.potrero_id,
        fecha_bano=fecha,
        proxima_fecha=proxima,
        metodo=datos.metodo,
        dosis_total_ml=datos.dosis_total_ml,
        litros_agua=datos.litros_agua,
        cantidad_animales=len(animales),
        costo_total=datos.costo_total,
        responsable_id=alcance.usuario.id,
        observaciones=datos.observaciones,
        device_id=datos.device_id,
        client_timestamp=datos.client_timestamp,
        client_timestamp_raw=datos.client_timestamp_raw,
    )
    if datos.id is not None:
        registro.id = datos.id
    alcance.sesion.add(registro)
    alcance.sesion.flush()

    alcance.sesion.add_all(
        [
            BanoAnimal(
                finca_id=alcance.finca_id,
                bano_id=registro.id,
                animal_id=animal.id,
                device_id=datos.device_id,
            )
            for animal in animales
        ]
    )
    alcance.sesion.flush()
    alcance.sesion.refresh(registro)
    return a_salida_bano(registro)


def listar_banos(
    alcance: AlcanceFinca,
    *,
    animal_id: uuid.UUID | None = None,
    grupo_id: uuid.UUID | None = None,
    vence_antes_de: date | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[BanoSalida], str | None, bool]:
    modo = MODO_DELTA if updated_since is not None else MODO_RECIENTE
    consulta = alcance.consultar(Bano, incluir_borrados=updated_since is not None)

    if updated_since is not None:
        consulta = consulta.where(Bano.updated_at > updated_since)
    if animal_id is not None:
        recibidos = sa.select(BanoAnimal.bano_id).where(
            BanoAnimal.animal_id == animal_id, BanoAnimal.is_deleted.is_(False)
        )
        consulta = consulta.where(Bano.id.in_(recibidos))
    if grupo_id is not None:
        consulta = consulta.where(Bano.grupo_id == grupo_id)
    if vence_antes_de is not None:
        consulta = consulta.where(
            Bano.proxima_fecha.is_not(None), Bano.proxima_fecha <= vence_antes_de
        )

    objeto_cursor = decodificar_cursor(cursor, modo) if cursor else None
    consulta = aplicar_orden_y_cursor(consulta, Bano, modo, objeto_cursor)
    filas = list(alcance.sesion.execute(consulta.limit(limite + 1)).unique().scalars())

    pagina, siguiente = armar_pagina(filas, limite, modo)
    return [a_salida_bano(b) for b in pagina], siguiente, siguiente is not None


def obtener_bano(alcance: AlcanceFinca, identificador: uuid.UUID) -> BanoSalida:
    registro = alcance.obtener(Bano, identificador)
    if registro is None:
        raise NoEncontrado("Ese baño no esta en tu finca.")
    return a_salida_bano(registro)


def animales_de_bano(alcance: AlcanceFinca, identificador: uuid.UUID) -> list[AnimalAplicado]:
    if alcance.obtener(Bano, identificador) is None:
        raise NoEncontrado("Ese baño no esta en tu finca.")

    filas = list(
        alcance.sesion.execute(
            alcance.consultar(BanoAnimal).where(BanoAnimal.bano_id == identificador)
        )
        .unique()
        .scalars()
    )
    return [
        AnimalAplicado(animal_id=f.animal_id, arete=f.animal.arete, nombre=f.animal.nombre)
        for f in filas
        if f.animal
    ]


def eliminar_bano(alcance: AlcanceFinca, identificador: uuid.UUID) -> None:
    registro = alcance.obtener(Bano, identificador)
    if registro is None:
        raise NoEncontrado("Ese baño no esta en tu finca.")

    ahora = datetime.now(UTC)
    registro.is_deleted = True
    registro.deleted_at = ahora
    registro.version += 1

    for puente in (
        alcance.sesion.execute(
            alcance.consultar(BanoAnimal).where(BanoAnimal.bano_id == identificador)
        )
        .unique()
        .scalars()
    ):
        puente.is_deleted = True
        puente.deleted_at = ahora
        puente.version += 1
    alcance.sesion.flush()
