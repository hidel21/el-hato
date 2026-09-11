"""Logica del modulo de Animales.

Todas las consultas salen de AlcanceFinca: ninguna funcion de aqui arma un
select() suelto, y por eso ninguna puede devolver datos de otra finca.
"""

import uuid
from datetime import UTC, date, datetime

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from app.dependencias.acceso import AlcanceFinca
from app.esquemas.animal import (
    AnimalActualizar,
    AnimalCrear,
    AnimalSalida,
    NodoGenealogia,
)
from app.modelos.animal import Animal
from app.modelos.enumeraciones import EstadoAnimal, Sexo
from app.modelos.territorio import Grupo, Potrero
from app.nucleo.errores import DatosInvalidos, NoEncontrado
from app.nucleo.paginacion import (
    MODO_DELTA,
    MODO_RECIENTE,
    Cursor,
    aplicar_orden_y_cursor,
    armar_pagina,
    decodificar_cursor,
)
from app.servicios import alertas, inventario

NIVELES_GENEALOGIA = 3


def a_salida(animal: Animal) -> AnimalSalida:
    salida = AnimalSalida.model_validate(animal)
    salida.grupo_nombre = animal.grupo.nombre if animal.grupo else None
    salida.potrero_nombre = animal.potrero.nombre if animal.potrero else None
    salida.madre_arete = animal.madre.arete if animal.madre else None
    salida.padre_arete = animal.padre.arete if animal.padre else None
    return salida


# ----------------------------------------------------------------------
# Listado
# ----------------------------------------------------------------------


def listar(
    alcance: AlcanceFinca,
    *,
    buscar: str | None = None,
    estado: EstadoAnimal | None = None,
    sexo: Sexo | None = None,
    grupo_id: uuid.UUID | None = None,
    potrero_id: uuid.UUID | None = None,
    solo_duplicados: bool = False,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[AnimalSalida], str | None, bool]:
    """Listado paginado por cursor.

    Con updated_since el listado cambia de orden y pasa a incluir los borrados:
    es el delta que consumira la sincronizacion, y un borrado tambien es un
    cambio que el dispositivo necesita conocer.
    """
    modo = MODO_DELTA if updated_since is not None else MODO_RECIENTE
    consulta = alcance.consultar(Animal, incluir_borrados=updated_since is not None)

    if updated_since is not None:
        consulta = consulta.where(Animal.updated_at > updated_since)
    if buscar:
        patron = f"%{buscar.strip()}%"
        consulta = consulta.where(sa.or_(Animal.arete.ilike(patron), Animal.nombre.ilike(patron)))
    if estado is not None:
        consulta = consulta.where(Animal.estado == estado)
    if sexo is not None:
        consulta = consulta.where(Animal.sexo == sexo)
    if grupo_id is not None:
        consulta = consulta.where(Animal.grupo_id == grupo_id)
    if potrero_id is not None:
        consulta = consulta.where(Animal.potrero_id == potrero_id)
    if solo_duplicados:
        consulta = consulta.where(Animal.arete_duplicado.is_(True))

    objeto_cursor: Cursor | None = None
    if cursor:
        objeto_cursor = decodificar_cursor(cursor, modo)

    consulta = aplicar_orden_y_cursor(consulta, Animal, modo, objeto_cursor)
    filas = list(alcance.sesion.execute(consulta.limit(limite + 1)).unique().scalars())

    pagina, siguiente = armar_pagina(filas, limite, modo)
    return [a_salida(animal) for animal in pagina], siguiente, siguiente is not None


def obtener(alcance: AlcanceFinca, animal_id: uuid.UUID) -> AnimalSalida:
    animal = alcance.obtener(Animal, animal_id)
    if animal is None:
        raise NoEncontrado("Ese animal no esta en tu finca.")
    return a_salida(animal)


# ----------------------------------------------------------------------
# Alta
# ----------------------------------------------------------------------


def _buscar_arete_canonico(alcance: AlcanceFinca, arete: str, excluir: uuid.UUID | None = None):
    """Devuelve el animal que hoy es dueño del arete, si lo hay."""
    consulta = alcance.consultar(Animal).where(
        Animal.arete == arete, Animal.arete_duplicado.is_(False)
    )
    if excluir is not None:
        consulta = consulta.where(Animal.id != excluir)
    return alcance.sesion.execute(consulta).unique().scalar_one_or_none()


def _validar_referencias(alcance: AlcanceFinca, datos: AnimalCrear | AnimalActualizar) -> None:
    """Grupo, potrero y padres tienen que ser de la misma finca."""
    comprobaciones = (
        (datos.grupo_id, Grupo, "El grupo no es de tu finca."),
        (datos.potrero_id, Potrero, "El potrero no es de tu finca."),
        (datos.madre_id, Animal, "La madre no esta en tu finca."),
        (datos.padre_id, Animal, "El padre no esta en tu finca."),
    )
    for identificador, modelo, mensaje in comprobaciones:
        if identificador is not None and alcance.obtener(modelo, identificador) is None:
            raise DatosInvalidos(mensaje)


def crear(alcance: AlcanceFinca, datos: AnimalCrear) -> AnimalSalida:
    """Alta de ficha. El servidor nunca rechaza un arete capturado en campo."""
    _validar_referencias(alcance, datos)

    if datos.fecha_nacimiento and datos.fecha_nacimiento > date.today():
        raise DatosInvalidos("La fecha de nacimiento no puede ser futura.")

    valores = datos.model_dump(exclude_none=True)
    valores.pop("id", None)

    animal = Animal(finca_id=alcance.finca_id, **valores)
    if datos.id is not None:
        animal.id = datos.id

    # Decision 1: si el arete ya tiene dueño, el registro entra igual, marcado.
    existente = _buscar_arete_canonico(alcance, animal.arete)
    animal.arete_duplicado = existente is not None

    alcance.sesion.add(animal)
    try:
        alcance.sesion.flush()
    except IntegrityError as error:
        # Carrera: otro dispositivo gano el arete entre la consulta y el flush.
        # Tampoco aqui se rechaza el dato: se marca y se vuelve a intentar.
        alcance.sesion.rollback()
        if "idx_animales_arete_unico" not in str(error.orig):
            raise
        animal = Animal(finca_id=alcance.finca_id, **valores)
        if datos.id is not None:
            animal.id = datos.id
        animal.arete_duplicado = True
        existente = _buscar_arete_canonico(alcance, animal.arete)
        alcance.sesion.add(animal)
        alcance.sesion.flush()

    if animal.arete_duplicado and existente is not None:
        alertas.alertar_arete_duplicado(alcance.sesion, animal, existente.id)

    alcance.sesion.flush()
    alcance.sesion.refresh(animal)
    inventario.agendar_refresco()
    return a_salida(animal)


# ----------------------------------------------------------------------
# Edicion y borrado
# ----------------------------------------------------------------------


def actualizar(
    alcance: AlcanceFinca, animal_id: uuid.UUID, datos: AnimalActualizar
) -> AnimalSalida:
    animal = alcance.obtener(Animal, animal_id)
    if animal is None:
        raise NoEncontrado("Ese animal no esta en tu finca.")

    _validar_referencias(alcance, datos)
    cambios = datos.model_dump(exclude_unset=True)

    if cambios.get("madre_id") == animal.id or cambios.get("padre_id") == animal.id:
        raise DatosInvalidos("Un animal no puede ser su propio padre o madre.")

    nuevo_arete = cambios.get("arete")
    if nuevo_arete and nuevo_arete != animal.arete:
        existente = _buscar_arete_canonico(alcance, nuevo_arete, excluir=animal.id)
        animal.arete_duplicado = existente is not None
        if existente is not None:
            alertas.alertar_arete_duplicado(alcance.sesion, animal, existente.id)

    for campo, valor in cambios.items():
        setattr(animal, campo, valor)

    animal.version += 1
    alcance.sesion.flush()
    alcance.sesion.refresh(animal)
    inventario.agendar_refresco()
    return a_salida(animal)


def eliminar(alcance: AlcanceFinca, animal_id: uuid.UUID) -> None:
    """Borrado logico. El fisico no existe en este sistema."""
    animal = alcance.obtener(Animal, animal_id)
    if animal is None:
        raise NoEncontrado("Ese animal no esta en tu finca.")

    animal.is_deleted = True
    animal.deleted_at = datetime.now(UTC)
    animal.version += 1
    alcance.sesion.flush()
    inventario.agendar_refresco()


# ----------------------------------------------------------------------
# Genealogia
# ----------------------------------------------------------------------


def genealogia(
    alcance: AlcanceFinca, animal_id: uuid.UUID, niveles: int = NIVELES_GENEALOGIA
) -> tuple[NodoGenealogia, int]:
    """Arbol de ancestros, hasta tres generaciones.

    Se resuelve por generacion y no por fila: como mucho son tres consultas,
    aunque el arbol este completo. Todo sale de AlcanceFinca, asi que un
    ancestro de otra finca simplemente no aparece.
    """
    raiz = alcance.obtener(Animal, animal_id)
    if raiz is None:
        raise NoEncontrado("Ese animal no esta en tu finca.")

    nodos: dict[uuid.UUID, NodoGenealogia] = {}
    padres_de: dict[uuid.UUID, tuple[uuid.UUID | None, uuid.UUID | None]] = {}

    def registrar(animal: Animal) -> NodoGenealogia:
        nodos[animal.id] = NodoGenealogia(
            id=animal.id,
            arete=animal.arete,
            nombre=animal.nombre,
            sexo=animal.sexo,
            raza=animal.raza,
            fecha_nacimiento=animal.fecha_nacimiento,
        )
        padres_de[animal.id] = (animal.madre_id, animal.padre_id)
        return nodos[animal.id]

    registrar(raiz)
    frontera = {raiz.id}

    for _ in range(niveles):
        por_buscar: set[uuid.UUID] = set()
        for identificador in frontera:
            for ancestro in padres_de[identificador]:
                if ancestro is not None and ancestro not in nodos:
                    por_buscar.add(ancestro)
        if not por_buscar:
            break

        consulta = alcance.consultar(Animal).where(Animal.id.in_(por_buscar))
        for animal in alcance.sesion.execute(consulta).unique().scalars():
            registrar(animal)
        frontera = por_buscar & nodos.keys()

    for identificador, nodo in nodos.items():
        madre_id, padre_id = padres_de[identificador]
        nodo.madre = nodos.get(madre_id) if madre_id else None
        nodo.padre = nodos.get(padre_id) if padre_id else None

    return nodos[raiz.id], niveles
