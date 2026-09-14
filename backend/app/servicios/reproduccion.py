"""Ciclo reproductivo: celo, servicio, diagnostico y parto.

El ciclo no termina en el diagnostico de preñez (decision 5). Sin el parto
registrado no hay intervalo entre partos, y el intervalo entre partos es EL
indicador de un hato de cria: cada dia de mas es un ternero menos por vaca en
su vida util.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

from app.dependencias.acceso import AlcanceFinca
from app.esquemas.reproduccion import (
    CeloCrear,
    CeloSalida,
    DiagnosticoCrear,
    DiagnosticoSalida,
    EventoReproductivo,
    HojaReproductiva,
    PartoCrear,
    PartoSalida,
    ServicioCrear,
    ServicioSalida,
)
from app.modelos.animal import Animal
from app.modelos.enumeraciones import EstadoAnimal, ResultadoParto, ResultadoPrenez, Sexo
from app.modelos.reproduccion import Celo, DiagnosticoPrenez, Parto, ServicioReproductivo
from app.nucleo.errores import DatosInvalidos, NoEncontrado
from app.nucleo.paginacion import (
    MODO_DELTA,
    MODO_RECIENTE,
    aplicar_orden_y_cursor,
    armar_pagina,
    decodificar_cursor,
)
from app.servicios import alertas, inventario

# Gestacion bovina. Varia unos dias por raza, pero 283 es el numero con el que
# se programa el parto en la practica.
DIAS_GESTACION = 283


def _hembra(alcance: AlcanceFinca, animal_id: uuid.UUID) -> Animal:
    animal = alcance.obtener(Animal, animal_id)
    if animal is None:
        raise DatosInvalidos("Ese animal no esta en tu finca.")
    if animal.sexo != Sexo.hembra:
        raise DatosInvalidos(f"{animal.arete} es macho: no puede entrar al ciclo reproductivo.")
    return animal


def _no_futura(fecha: date, quees: str) -> date:
    if fecha > date.today():
        raise DatosInvalidos(f"{quees} no puede ser una fecha futura.")
    return fecha


def _paginar(alcance: AlcanceFinca, modelo, filtros, updated_since, cursor, limite):
    modo = MODO_DELTA if updated_since is not None else MODO_RECIENTE
    consulta = alcance.consultar(modelo, incluir_borrados=updated_since is not None)
    if updated_since is not None:
        consulta = consulta.where(modelo.updated_at > updated_since)
    for condicion in filtros:
        consulta = consulta.where(condicion)

    objeto_cursor = decodificar_cursor(cursor, modo) if cursor else None
    consulta = aplicar_orden_y_cursor(consulta, modelo, modo, objeto_cursor)
    filas = list(alcance.sesion.execute(consulta.limit(limite + 1)).unique().scalars())
    return armar_pagina(filas, limite, modo)


# ----------------------------------------------------------------------
# Celo
# ----------------------------------------------------------------------


def a_salida_celo(celo: Celo) -> CeloSalida:
    salida = CeloSalida.model_validate(celo)
    salida.animal_arete = celo.animal.arete if celo.animal else None
    return salida


def registrar_celo(alcance: AlcanceFinca, datos: CeloCrear) -> CeloSalida:
    animal = _hembra(alcance, datos.animal_id)
    fecha = _no_futura(datos.fecha_celo or date.today(), "El celo")

    celo = Celo(
        finca_id=alcance.finca_id,
        animal_id=animal.id,
        fecha_celo=fecha,
        metodo=datos.metodo,
        intensidad=datos.intensidad,
        responsable_id=alcance.usuario.id,
        observaciones=datos.observaciones,
        device_id=datos.device_id,
        client_timestamp=datos.client_timestamp,
        client_timestamp_raw=datos.client_timestamp_raw,
    )
    if datos.id is not None:
        celo.id = datos.id
    alcance.sesion.add(celo)
    alcance.sesion.flush()
    alcance.sesion.refresh(celo)
    return a_salida_celo(celo)


def listar_celos(
    alcance: AlcanceFinca,
    *,
    animal_id: uuid.UUID | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[CeloSalida], str | None, bool]:
    filtros = [Celo.animal_id == animal_id] if animal_id else []
    pagina, siguiente = _paginar(alcance, Celo, filtros, updated_since, cursor, limite)
    return [a_salida_celo(c) for c in pagina], siguiente, siguiente is not None


# ----------------------------------------------------------------------
# Servicio
# ----------------------------------------------------------------------


def a_salida_servicio(servicio: ServicioReproductivo) -> ServicioSalida:
    salida = ServicioSalida.model_validate(servicio)
    salida.animal_arete = servicio.animal.arete if servicio.animal else None
    salida.toro_arete = servicio.toro.arete if servicio.toro else None
    return salida


def registrar_servicio(alcance: AlcanceFinca, datos: ServicioCrear) -> ServicioSalida:
    animal = _hembra(alcance, datos.animal_id)
    fecha = _no_futura(datos.fecha_servicio or date.today(), "El servicio")

    if datos.toro_id is not None:
        toro = alcance.obtener(Animal, datos.toro_id)
        if toro is None:
            raise DatosInvalidos("Ese toro no esta en tu finca.")
        if toro.sexo != Sexo.macho:
            raise DatosInvalidos(f"{toro.arete} es hembra: no puede servir.")
    if datos.celo_id is not None and alcance.obtener(Celo, datos.celo_id) is None:
        raise DatosInvalidos("Ese celo no esta en tu finca.")

    servicio = ServicioReproductivo(
        finca_id=alcance.finca_id,
        animal_id=animal.id,
        celo_id=datos.celo_id,
        tipo=datos.tipo,
        fecha_servicio=fecha,
        toro_id=datos.toro_id,
        pajilla_codigo=datos.pajilla_codigo,
        inseminador_id=datos.inseminador_id or alcance.usuario.id,
        fecha_estimada_parto=fecha + timedelta(days=DIAS_GESTACION),
        costo=datos.costo,
        observaciones=datos.observaciones,
        device_id=datos.device_id,
        client_timestamp=datos.client_timestamp,
        client_timestamp_raw=datos.client_timestamp_raw,
    )
    if datos.id is not None:
        servicio.id = datos.id
    alcance.sesion.add(servicio)
    alcance.sesion.flush()
    alcance.sesion.refresh(servicio)
    return a_salida_servicio(servicio)


def listar_servicios(
    alcance: AlcanceFinca,
    *,
    animal_id: uuid.UUID | None = None,
    toro_id: uuid.UUID | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[ServicioSalida], str | None, bool]:
    filtros = []
    if animal_id:
        filtros.append(ServicioReproductivo.animal_id == animal_id)
    if toro_id:
        filtros.append(ServicioReproductivo.toro_id == toro_id)
    pagina, siguiente = _paginar(
        alcance, ServicioReproductivo, filtros, updated_since, cursor, limite
    )
    return [a_salida_servicio(s) for s in pagina], siguiente, siguiente is not None


# ----------------------------------------------------------------------
# Diagnostico
# ----------------------------------------------------------------------


def a_salida_diagnostico(diagnostico: DiagnosticoPrenez) -> DiagnosticoSalida:
    salida = DiagnosticoSalida.model_validate(diagnostico)
    salida.animal_arete = diagnostico.animal.arete if diagnostico.animal else None
    return salida


def registrar_diagnostico(alcance: AlcanceFinca, datos: DiagnosticoCrear) -> DiagnosticoSalida:
    animal = _hembra(alcance, datos.animal_id)
    fecha = _no_futura(datos.fecha_diagnostico or date.today(), "El diagnostico")

    servicio = None
    if datos.servicio_id is not None:
        servicio = alcance.obtener(ServicioReproductivo, datos.servicio_id)
        if servicio is None:
            raise DatosInvalidos("Ese servicio no esta en tu finca.")
    else:
        # Sin servicio indicado se toma el ultimo anterior al diagnostico: es
        # lo que el veterinario da por hecho cuando palpa en la manga.
        servicio = (
            alcance.sesion.execute(
                alcance.consultar(ServicioReproductivo)
                .where(
                    ServicioReproductivo.animal_id == animal.id,
                    ServicioReproductivo.fecha_servicio <= fecha,
                )
                .order_by(ServicioReproductivo.fecha_servicio.desc())
                .limit(1)
            )
            .unique()
            .scalar_one_or_none()
        )

    # La fecha estimada de parto sale del servicio; si no hay, de los dias de
    # gestacion que estimo quien palpo.
    estimada = None
    if datos.resultado == ResultadoPrenez.prenada:
        if servicio is not None:
            estimada = servicio.fecha_estimada_parto
        elif datos.dias_gestacion:
            estimada = fecha + timedelta(days=DIAS_GESTACION - datos.dias_gestacion)

    diagnostico = DiagnosticoPrenez(
        finca_id=alcance.finca_id,
        animal_id=animal.id,
        servicio_id=servicio.id if servicio else None,
        fecha_diagnostico=fecha,
        resultado=datos.resultado,
        metodo=datos.metodo,
        dias_gestacion=datos.dias_gestacion,
        fecha_estimada_parto=estimada,
        responsable_id=alcance.usuario.id,
        observaciones=datos.observaciones,
        device_id=datos.device_id,
        client_timestamp=datos.client_timestamp,
        client_timestamp_raw=datos.client_timestamp_raw,
    )
    if datos.id is not None:
        diagnostico.id = datos.id
    alcance.sesion.add(diagnostico)
    alcance.sesion.flush()
    alcance.sesion.refresh(diagnostico)
    return a_salida_diagnostico(diagnostico)


def listar_diagnosticos(
    alcance: AlcanceFinca,
    *,
    animal_id: uuid.UUID | None = None,
    resultado: ResultadoPrenez | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[DiagnosticoSalida], str | None, bool]:
    filtros = []
    if animal_id:
        filtros.append(DiagnosticoPrenez.animal_id == animal_id)
    if resultado:
        filtros.append(DiagnosticoPrenez.resultado == resultado)
    pagina, siguiente = _paginar(alcance, DiagnosticoPrenez, filtros, updated_since, cursor, limite)
    return [a_salida_diagnostico(d) for d in pagina], siguiente, siguiente is not None


# ----------------------------------------------------------------------
# Parto: donde se cierra el ciclo (decision 5)
# ----------------------------------------------------------------------


def _parto_anterior(alcance: AlcanceFinca, madre_id: uuid.UUID, antes_de: date, excluir=None):
    consulta = (
        alcance.consultar(Parto)
        .where(Parto.madre_id == madre_id, Parto.fecha_parto < antes_de)
        .order_by(Parto.fecha_parto.desc())
        .limit(1)
    )
    if excluir is not None:
        consulta = consulta.where(Parto.id != excluir)
    return alcance.sesion.execute(consulta).unique().scalar_one_or_none()


def a_salida_parto(alcance: AlcanceFinca, parto: Parto) -> PartoSalida:
    salida = PartoSalida.model_validate(parto)
    salida.madre_arete = parto.madre.arete if parto.madre else None
    salida.cria_arete = parto.cria.arete if parto.cria else None

    anterior = _parto_anterior(alcance, parto.madre_id, parto.fecha_parto, excluir=parto.id)
    if anterior is not None:
        salida.intervalo_partos_dias = (parto.fecha_parto - anterior.fecha_parto).days
    return salida


def registrar_parto(alcance: AlcanceFinca, datos: PartoCrear) -> PartoSalida:
    """Cierra la gestacion y, si se pide, abre la ficha del ternero.

    Crear la cria aqui evita capturar el nacimiento dos veces y deja la
    genealogia armada sola: madre la que pario, padre el toro del servicio.
    """
    madre = _hembra(alcance, datos.madre_id)
    fecha = _no_futura(datos.fecha_parto or date.today(), "El parto")

    if datos.cria is not None and datos.cria_id is not None:
        raise DatosInvalidos("O creas la ficha de la cria o enlazas una que ya existe, no las dos.")

    diagnostico = None
    if datos.diagnostico_id is not None:
        diagnostico = alcance.obtener(DiagnosticoPrenez, datos.diagnostico_id)
        if diagnostico is None:
            raise DatosInvalidos("Ese diagnostico no esta en tu finca.")

    cria = None
    if datos.cria_id is not None:
        cria = alcance.obtener(Animal, datos.cria_id)
        if cria is None:
            raise DatosInvalidos("Esa cria no esta en tu finca.")
    elif datos.cria is not None:
        if datos.resultado != ResultadoParto.vivo:
            raise DatosInvalidos(
                "Solo se abre ficha cuando la cria nace viva. Registra el parto sin ficha."
            )
        cria = _abrir_ficha_de_cria(alcance, madre, datos, fecha)

    parto = Parto(
        finca_id=alcance.finca_id,
        madre_id=madre.id,
        diagnostico_id=diagnostico.id if diagnostico else None,
        cria_id=cria.id if cria else None,
        fecha_parto=fecha,
        resultado=datos.resultado,
        dificultad=datos.dificultad,
        peso_nacimiento_kg=datos.peso_nacimiento_kg
        or (datos.cria.peso_nacimiento_kg if datos.cria else None),
        responsable_id=alcance.usuario.id,
        observaciones=datos.observaciones,
        device_id=datos.device_id,
        client_timestamp=datos.client_timestamp,
        client_timestamp_raw=datos.client_timestamp_raw,
    )
    if datos.id is not None:
        parto.id = datos.id
    alcance.sesion.add(parto)
    alcance.sesion.flush()
    alcance.sesion.refresh(parto)
    inventario.agendar_refresco()
    return a_salida_parto(alcance, parto)


def _abrir_ficha_de_cria(
    alcance: AlcanceFinca, madre: Animal, datos: PartoCrear, fecha: date
) -> Animal:
    """Da de alta al ternero con la genealogia ya puesta.

    El arete repetido no se rechaza, igual que en el alta normal (decision 1):
    entra marcado y levanta una alerta.
    """
    ultimo_servicio = (
        alcance.sesion.execute(
            alcance.consultar(ServicioReproductivo)
            .where(
                ServicioReproductivo.animal_id == madre.id,
                ServicioReproductivo.fecha_servicio < fecha,
            )
            .order_by(ServicioReproductivo.fecha_servicio.desc())
            .limit(1)
        )
        .unique()
        .scalar_one_or_none()
    )

    cria = Animal(
        finca_id=alcance.finca_id,
        arete=datos.cria.arete,
        nombre=datos.cria.nombre,
        sexo=datos.cria.sexo,
        raza=madre.raza,
        fecha_nacimiento=fecha,
        fecha_ingreso=fecha,
        origen="nacimiento",
        estado=EstadoAnimal.activo,
        madre_id=madre.id,
        padre_id=ultimo_servicio.toro_id if ultimo_servicio else None,
        grupo_id=None,
        potrero_id=madre.potrero_id,
        peso_nacimiento_kg=datos.cria.peso_nacimiento_kg or datos.peso_nacimiento_kg,
        peso_actual_kg=datos.cria.peso_nacimiento_kg or datos.peso_nacimiento_kg,
        device_id=datos.device_id,
    )

    existente = (
        alcance.sesion.execute(
            alcance.consultar(Animal).where(
                Animal.arete == cria.arete, Animal.arete_duplicado.is_(False)
            )
        )
        .unique()
        .scalar_one_or_none()
    )
    cria.arete_duplicado = existente is not None

    alcance.sesion.add(cria)
    alcance.sesion.flush()
    if existente is not None:
        alertas.alertar_arete_duplicado(alcance.sesion, cria, existente.id)
    return cria


def listar_partos(
    alcance: AlcanceFinca,
    *,
    madre_id: uuid.UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    updated_since: datetime | None = None,
    cursor: str | None = None,
    limite: int = 50,
) -> tuple[list[PartoSalida], str | None, bool]:
    filtros = []
    if madre_id:
        filtros.append(Parto.madre_id == madre_id)
    if desde:
        filtros.append(Parto.fecha_parto >= desde)
    if hasta:
        filtros.append(Parto.fecha_parto <= hasta)
    pagina, siguiente = _paginar(alcance, Parto, filtros, updated_since, cursor, limite)
    return [a_salida_parto(alcance, p) for p in pagina], siguiente, siguiente is not None


def obtener_parto(alcance: AlcanceFinca, parto_id: uuid.UUID) -> PartoSalida:
    parto = alcance.obtener(Parto, parto_id)
    if parto is None:
        raise NoEncontrado("Ese parto no esta en tu finca.")
    return a_salida_parto(alcance, parto)


def eliminar(alcance: AlcanceFinca, modelo, identificador: uuid.UUID, quees: str) -> None:
    """Borrado logico de cualquier registro del ciclo."""
    registro = alcance.obtener(modelo, identificador)
    if registro is None:
        raise NoEncontrado(f"{quees} no esta en tu finca.")

    registro.is_deleted = True
    registro.deleted_at = datetime.now(UTC)
    registro.version += 1
    alcance.sesion.flush()


# ----------------------------------------------------------------------
# Hoja reproductiva
# ----------------------------------------------------------------------

DESCRIPCIONES = {
    "sin_registros": "Sin registros reproductivos",
    "vacia": "Vacía",
    "en_servicio": "Servida, esperando diagnóstico",
    "prenada": "Preñada",
    "parida": "Parió, aún sin nuevo servicio",
}

ETIQUETA_DIAGNOSTICO = {
    ResultadoPrenez.prenada: "preñada",
    ResultadoPrenez.vacia: "vacía",
    ResultadoPrenez.dudoso: "dudoso",
}


def hoja_reproductiva(alcance: AlcanceFinca, animal_id: uuid.UUID) -> HojaReproductiva:
    """Todo el historial de una hembra y en que punto del ciclo esta.

    Es una lectura de conveniencia: en Fase 2 el dispositivo puede derivar lo
    mismo con los datos que ya tiene, porque todo sale de las fichas de ese
    animal y no de agregaciones de la finca (decision 6).
    """
    animal = alcance.obtener(Animal, animal_id)
    if animal is None:
        raise NoEncontrado("Ese animal no esta en tu finca.")

    celos = list(
        alcance.sesion.execute(
            alcance.consultar(Celo).where(Celo.animal_id == animal_id).order_by(Celo.fecha_celo)
        )
        .unique()
        .scalars()
    )
    servicios = list(
        alcance.sesion.execute(
            alcance.consultar(ServicioReproductivo)
            .where(ServicioReproductivo.animal_id == animal_id)
            .order_by(ServicioReproductivo.fecha_servicio)
        )
        .unique()
        .scalars()
    )
    diagnosticos = list(
        alcance.sesion.execute(
            alcance.consultar(DiagnosticoPrenez)
            .where(DiagnosticoPrenez.animal_id == animal_id)
            .order_by(DiagnosticoPrenez.fecha_diagnostico)
        )
        .unique()
        .scalars()
    )
    partos = list(
        alcance.sesion.execute(
            alcance.consultar(Parto).where(Parto.madre_id == animal_id).order_by(Parto.fecha_parto)
        )
        .unique()
        .scalars()
    )

    eventos: list[EventoReproductivo] = []
    for celo in celos:
        eventos.append(
            EventoReproductivo(
                tipo="celo",
                fecha=celo.fecha_celo,
                titulo="Celo detectado",
                detalle=f"Intensidad {celo.intensidad}" if celo.intensidad else celo.metodo.value,
                referencia_id=celo.id,
            )
        )
    for servicio in servicios:
        nombre = {"monta_natural": "Monta natural", "inseminacion": "Inseminación"}.get(
            servicio.tipo, servicio.tipo
        )
        eventos.append(
            EventoReproductivo(
                tipo="servicio",
                fecha=servicio.fecha_servicio,
                titulo=f"Servicio · {nombre}",
                detalle=f"Toro {servicio.toro.arete}" if servicio.toro else servicio.pajilla_codigo,
                referencia_id=servicio.id,
            )
        )
    for diagnostico in diagnosticos:
        eventos.append(
            EventoReproductivo(
                tipo="diagnostico",
                fecha=diagnostico.fecha_diagnostico,
                titulo=f"Diagnóstico · {ETIQUETA_DIAGNOSTICO[diagnostico.resultado]}",
                detalle=diagnostico.metodo,
                referencia_id=diagnostico.id,
            )
        )
    for parto in partos:
        eventos.append(
            EventoReproductivo(
                tipo="parto",
                fecha=parto.fecha_parto,
                titulo=f"Parto · {parto.resultado.value}",
                detalle=f"Cría {parto.cria.arete}" if parto.cria else parto.dificultad.value,
                referencia_id=parto.id,
            )
        )
    eventos.sort(key=lambda evento: evento.fecha)

    ultimo_parto = partos[-1] if partos else None
    ultimo_servicio = servicios[-1] if servicios else None
    ultimo_diagnostico = diagnosticos[-1] if diagnosticos else None

    estado = _estado_reproductivo(ultimo_parto, ultimo_servicio, ultimo_diagnostico)

    # Dias abiertos: desde el ultimo parto hasta el servicio que lo siguio, o
    # hasta hoy si todavia no la han vuelto a servir. Cada dia cuesta dinero.
    dias_abiertos = None
    if ultimo_parto is not None:
        posterior = next(
            (s for s in servicios if s.fecha_servicio > ultimo_parto.fecha_parto), None
        )
        hasta = posterior.fecha_servicio if posterior else date.today()
        dias_abiertos = (hasta - ultimo_parto.fecha_parto).days

    intervalos = [
        (partos[i].fecha_parto - partos[i - 1].fecha_parto).days for i in range(1, len(partos))
    ]

    estimada = None
    if estado == "prenada":
        if ultimo_diagnostico and ultimo_diagnostico.fecha_estimada_parto:
            estimada = ultimo_diagnostico.fecha_estimada_parto
        elif ultimo_servicio:
            estimada = ultimo_servicio.fecha_estimada_parto
    elif estado == "en_servicio" and ultimo_servicio:
        estimada = ultimo_servicio.fecha_estimada_parto

    return HojaReproductiva(
        animal_id=animal.id,
        arete=animal.arete,
        estado=estado,
        descripcion_estado=DESCRIPCIONES[estado],
        ultimo_celo=celos[-1].fecha_celo if celos else None,
        ultimo_servicio=ultimo_servicio.fecha_servicio if ultimo_servicio else None,
        ultimo_diagnostico=ultimo_diagnostico.resultado if ultimo_diagnostico else None,
        fecha_estimada_parto=estimada,
        ultimo_parto=ultimo_parto.fecha_parto if ultimo_parto else None,
        dias_abiertos=dias_abiertos,
        partos_totales=len(partos),
        intervalo_promedio_dias=round(sum(intervalos) / len(intervalos)) if intervalos else None,
        eventos=eventos,
    )


def _estado_reproductivo(ultimo_parto, ultimo_servicio, ultimo_diagnostico) -> str:
    """En que punto del ciclo esta, mirando cual fue el ultimo hecho."""
    fechas = {
        "parida": ultimo_parto.fecha_parto if ultimo_parto else None,
        "servicio": ultimo_servicio.fecha_servicio if ultimo_servicio else None,
        "diagnostico": ultimo_diagnostico.fecha_diagnostico if ultimo_diagnostico else None,
    }
    if not any(fechas.values()):
        return "sin_registros"

    ultimo = max((f, k) for k, f in fechas.items() if f is not None)[1]
    if ultimo == "parida":
        return "parida"
    if ultimo == "servicio":
        return "en_servicio"
    return "prenada" if ultimo_diagnostico.resultado == ResultadoPrenez.prenada else "vacia"
