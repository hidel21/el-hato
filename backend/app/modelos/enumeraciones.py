"""Enumeraciones del dominio. El valor que se guarda en Postgres es el texto."""

import enum

import sqlalchemy as sa


class RolUsuario(enum.StrEnum):
    administrador = "administrador"
    veterinario = "veterinario"
    capataz = "capataz"


class Sexo(enum.StrEnum):
    hembra = "hembra"
    macho = "macho"


class EstadoAnimal(enum.StrEnum):
    activo = "activo"
    vendido = "vendido"
    muerto = "muerto"
    descartado = "descartado"
    en_engorde = "en_engorde"


class EtapaGrupo(enum.StrEnum):
    ternero = "ternero"
    destete = "destete"
    levante = "levante"
    engorde = "engorde"
    vientre = "vientre"
    toro = "toro"
    descarte = "descarte"


class PropositoGrupo(enum.StrEnum):
    cria = "cria"
    levante = "levante"
    engorde = "engorde"
    leche = "leche"
    doble_proposito = "doble_proposito"
    manejo = "manejo"


class MetodoCelo(enum.StrEnum):
    observacion = "observacion"
    parche = "parche"
    podometro = "podometro"
    monta_registrada = "monta_registrada"
    otro = "otro"


class ResultadoPrenez(enum.StrEnum):
    prenada = "prenada"
    vacia = "vacia"
    dudoso = "dudoso"


class ResultadoParto(enum.StrEnum):
    vivo = "vivo"
    muerto = "muerto"
    aborto = "aborto"
    gemelar = "gemelar"


class DificultadParto(enum.StrEnum):
    normal = "normal"
    asistido = "asistido"
    cesarea = "cesarea"
    distocia = "distocia"


class TipoPasto(enum.StrEnum):
    brachiaria = "brachiaria"
    estrella = "estrella"
    guinea = "guinea"
    kikuyo = "kikuyo"
    angleton = "angleton"
    pasto_natural = "pasto_natural"
    mezcla = "mezcla"
    otro = "otro"


class TipoAlerta(enum.StrEnum):
    vacunacion = "vacunacion"
    bano = "bano"
    parto = "parto"
    celo = "celo"
    peso = "peso"
    rotacion = "rotacion"
    inventario = "inventario"
    otro = "otro"


class EstadoAlerta(enum.StrEnum):
    pendiente = "pendiente"
    vencida = "vencida"
    atendida = "atendida"
    descartada = "descartada"


class CategoriaGasto(enum.StrEnum):
    alimento = "alimento"
    medicamento = "medicamento"
    veterinario = "veterinario"
    mano_obra = "mano_obra"
    insumo = "insumo"
    transporte = "transporte"
    mantenimiento = "mantenimiento"
    otro = "otro"


class OperacionSync(enum.StrEnum):
    insert = "insert"
    update = "update"
    delete = "delete"


class EstadoSync(enum.StrEnum):
    pendiente = "pendiente"
    enviando = "enviando"
    enviado = "enviado"
    error = "error"


# Nombre del tipo en Postgres para cada enumeracion de Python.
NOMBRES_EN_POSTGRES: dict[type[enum.Enum], str] = {
    RolUsuario: "user_role_enum",
    Sexo: "sexo_enum",
    EstadoAnimal: "animal_estado_enum",
    EtapaGrupo: "grupo_etapa_enum",
    PropositoGrupo: "grupo_proposito_enum",
    MetodoCelo: "celo_metodo_enum",
    ResultadoPrenez: "prenez_resultado_enum",
    ResultadoParto: "parto_resultado_enum",
    DificultadParto: "parto_dificultad_enum",
    TipoPasto: "potrero_tipo_pasto_enum",
    TipoAlerta: "alerta_tipo_enum",
    EstadoAlerta: "alerta_estado_enum",
    CategoriaGasto: "gasto_categoria_enum",
    OperacionSync: "sync_operation_enum",
    EstadoSync: "sync_status_enum",
}


def tipo_enum(enumeracion: type[enum.Enum]) -> sa.Enum:
    """Columna de enumeracion nativa de Postgres, guardando el valor y no el nombre."""
    return sa.Enum(
        enumeracion,
        name=NOMBRES_EN_POSTGRES[enumeracion],
        values_callable=lambda e: [miembro.value for miembro in e],
        native_enum=True,
    )
